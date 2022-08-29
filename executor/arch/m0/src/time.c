#include "config.h"
#include "lib/printf.h"
#include <stdint.h>

#include "experiment/exp_time_runner.h"

#ifdef RUN_TIME

void run_time_experiment(void)
{
    uint32_t t1 = time_run(1);
    uint32_t t2 = time_run(2);

    printf("T1 = %d\n", t1);
    printf("T2 = %d\n", t2);
}

#endif // RUN_TIME
