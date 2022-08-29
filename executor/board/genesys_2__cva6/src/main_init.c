#include "uart_leg.h"

int main();

int _main_init()
{
/*
    init_uart(50000000, 115200);
    print_uart("\r\n\r\nHello World!\r\n");

    print_uart("And a print loop...\r\n");
    while (0)
    {
        print_uart(".");
        for (int i = 0; i < 10000000; i++);
        // do nothing
    }
*/
    return main();
}

void handle_trap(void)
{
    // print_uart("trap\r\n");
}
