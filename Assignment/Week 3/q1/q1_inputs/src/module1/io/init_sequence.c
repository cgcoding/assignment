#include <stdio.h>
#include <newlib.h>
#include "core/adapter.h"

int run_init_sequence(void) {
    struct adapter_config cfg = {5, "https://init.example"};
    return init_adapter(&cfg);
}
