#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "mpi.h"


// Funções a integrar 
double f1(double x) { return sin(x); }
double f2(double x) { return exp(-x * x); }
double f3(double x) { return 1.0 / (1.0 + x * x); }

typedef double (*func_t)(double);

// Soma local usando a regra do trapézio, intervalo [local_a, local_b], com local_n trapézios de largura h
double trap_local(double local_a, double local_b, long local_n,
                  double h, func_t f)
{
    double sum = (f(local_a) + f(local_b)) / 2.0;
    for (long i = 1; i < local_n; i++)
        sum += f(local_a + i * h);
    return sum * h;
}


int main(int argc, char *argv[])
{
    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Parâmetros de integração (definidos pelo rank 0, depois broadcast)
    int    func_id = 1;
    double a = 0.0, b = 1.0;
    long   n = 1000000L;   // default: 1 milhão de trapezios 

    if (rank == 0) {
        if (argc == 5) {
            func_id = atoi(argv[1]);
            a       = atof(argv[2]);
            b       = atof(argv[3]);
            n       = atol(argv[4]);
        } else if (argc != 1) {
            fprintf(stderr,
                "Usage: mpirun -np <p> ./trap_mpi <func> <a> <b> <n>\n"
                "  func: 1=sin(x)  2=exp(-x^2)  3=1/(1+x^2)\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        // Ajusta n para ser divisível por size, se necessário
        if (n % size != 0) {
            n = ((n / size) + 1) * size;
            fprintf(stderr,
                "[rank 0] n adjusted to %ld to be divisible by %d\n",
                n, size);
        }
    }

    // Tempo total (inclui overhead de comunicação)
    double t_start_total = MPI_Wtime();   

    MPI_Bcast(&func_id, 1, MPI_INT,    0, MPI_COMM_WORLD);
    MPI_Bcast(&a,       1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(&b,       1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(&n,       1, MPI_LONG,   0, MPI_COMM_WORLD);

    // Escolher função
    /*  Functions:
        f1(x) = sin(x)
        f2(x) = exp(-x^2)
        f3(x) = 1 / (1 + x^2) */
    func_t f;
    const char *fname;
    switch (func_id) {
        case 2:  f = f2; fname = "exp(-x^2)";   break;
        case 3:  f = f3; fname = "1/(1+x^2)";   break;
        default: f = f1; fname = "sin(x)";       break;
    }

    // Cálculo de subintervalos para cada rank
    double h       = (b - a) / (double)n;
    long   local_n = n / size;
    double local_a = a + rank * local_n * h;
    double local_b = local_a + local_n * h;

    // Tempo de computação (apenas a parte local, sem comunicação)
    double t_comp_start = MPI_Wtime();
    double local_sum    = trap_local(local_a, local_b, local_n, h, f);
    double t_comp_end   = MPI_Wtime();
    double t_compute    = t_comp_end - t_comp_start;

    // Reduce: soma local_sum de todos os ranks para total_sum no rank 0
    double total_sum = 0.0;
    MPI_Reduce(&local_sum, &total_sum, 1, MPI_DOUBLE,
               MPI_SUM, 0, MPI_COMM_WORLD);

    double t_end_total = MPI_Wtime();
    double t_total     = t_end_total - t_start_total;

    // Juntar o tempo máximo de computação entre os ranks
    double t_compute_max = 0.0;
    MPI_Reduce(&t_compute, &t_compute_max, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    // Print
    if (rank == 0) {
        // Formato CSV: p, func, a, b, n, result, T_total, T_compute
        printf("%d,%s,%.4f,%.4f,%ld,%.15f,%.9f,%.9f\n",
               size, fname, a, b, n,
               total_sum, t_total, t_compute_max);
        fflush(stdout);
    }

    MPI_Finalize();
    return 0;
}

// Uso: 
//      mpirun -np <p> ./trap_mpi <func> <a> <b> <n>
//          func : 1=sin(x)  2=exp(-x^2)  3=1/(1+x^2)
//          a, b : integration interval
//          n    : number of trapezoids (must be divisible by p)
 
