#include <stdio.h>

int main(void) {
    /* A simple for loop */
    for (int i = 1; i <= 5; i++) {
        printf("Counting: %d\n", i);
    }

    /* Read a name from the console and greet it */
    char name[64];
    printf("\nWhat is your name?\n");
    scanf("%63s", name);
    printf("Welcome, %s!\n", name);

    return 0;
}
