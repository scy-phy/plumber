
#include "uart_leg.h"

void uart_init()
{
    init_uart(50000000, 115200);
    //print_uart("\r\n\r\nHello World!\r\n");
}

void write_serial(char a);

void uart_putchar(char c) {
    write_serial(c);
}

char uart_getchar() {
    //return 'A';
    while(1);
}


