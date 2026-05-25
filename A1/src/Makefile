CC      = mpicc.openmpi
CFLAGS  = -O2 -Wall -Wextra
LDFLAGS = -lm
TARGET  = trap_mpi

.PHONY: all clean run_experiments

all: $(TARGET)

$(TARGET): trap_mpi.c
	$(CC) $(CFLAGS) -o $(TARGET) trap_mpi.c $(LDFLAGS)

# Run all experiments and save raw CSV
run_experiments: $(TARGET)
	bash run_experiments.sh

clean:
	rm -f $(TARGET) results_raw.csv