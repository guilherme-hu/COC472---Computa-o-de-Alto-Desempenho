set -euo pipefail

BINARY="./trap_mpi"
OUTPUT="results_raw.csv"
RUNS=5   # repetições por config (usamos a mediana para reduzir ruído)

if [ ! -x "$BINARY" ]; then
    echo "ERROR: $BINARY não encontrado. Rode 'make' primeiro."
    exit 1
fi

# Detecta se MPI suporta oversubscribe (OpenMPI) ou não (MPICH)
EXTRA_FLAGS=""
if mpirun.openmpi --oversubscribe -np 1 echo "" > /dev/null 2>&1; then
    EXTRA_FLAGS="--oversubscribe"
    echo "[INFO] OpenMPI detectado — usando --oversubscribe"
else
    echo "[INFO] MPICH detectado — sem flag extra"
fi

# Número de processos a testar 
PROCS=(1 2 4 8 16)

# Funções: id a b   
declare -a FUNCS=(
    "1 0.0 3.14159265358979"   # sin(x) de 0 a pi
    "2 0.0 2.0"                # exp(-x^2) de 0 a 2
    "3 0.0 10.0"               # 1/(1+x^2) de 0 a 10
)

# n: mesma carga total (strong scaling) 
# Deve ser divisível por 16 = lcm(1,2,4,8,16)
N_VALUES=(16000000 160000000)

# Cabeçalho CSV 
echo "p,func,a,b,n,result,T_total,T_compute" > "$OUTPUT"

# Loop main
for func_line in "${FUNCS[@]}"; do
    read -r fid fa fb <<< "$func_line"

    for n in "${N_VALUES[@]}"; do
        for p in "${PROCS[@]}"; do

            printf "  func=%-2s  n=%-11d  p=%-3d  ... " "$fid" "$n" "$p"

            tmp=$(mktemp)

            for _rep in $(seq 1 $RUNS); do
                mpirun.openmpi $EXTRA_FLAGS -np "$p" \
                    "$BINARY" "$fid" "$fa" "$fb" "$n" >> "$tmp" 2>/dev/null
            done

            # Mediana: ordena por T_compute (campo 8) e pega linha central
            median=$(sort -t',' -k8 -n "$tmp" \
                     | awk -v r="$RUNS" 'NR==int((r+1)/2){print}')
            echo "$median" >> "$OUTPUT"
            echo "OK — $median"

            rm -f "$tmp"
        done
    done
done

echo ""
echo "Experimentos concluídos. Resultados em: $OUTPUT"

#   chmod +x run_experiments.sh
#   ./run_experiments.sh