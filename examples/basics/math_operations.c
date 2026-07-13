#include <stdio.h>

int main(void) {
    int a = 10;
    int b = 3;

    printf("Addition: %d\n", a + b);
    printf("Subtraction: %d\n", a - b);
    printf("Multiplication: %d\n", a * b);
    printf("Integer division: %d\n", a / b);
    printf("Float division: %.4f\n", (double)a / b);
    printf("Modulus (remainder): %d\n", a % b);

    /* Shorthand assignment */
    int x = 5;
    x += 2; /* Same as x = x + 2 */
    printf("x after += 2: %d\n", x);

    return 0;
}
