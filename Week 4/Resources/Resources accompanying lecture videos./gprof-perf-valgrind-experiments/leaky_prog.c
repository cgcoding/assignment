// fixed_tricky_leak.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * Duplicate the input string and trim trailing spaces.
 * If the trimmed string is longer than 10 characters,
 * clean up and return NULL.
 */
char* duplicate_and_trim(const char* s) {
    size_t orig_len = strlen(s);
    char *buffer = malloc(orig_len + 1);
    if (!buffer) return NULL;        
    strcpy(buffer, s);

    size_t len = strlen(buffer);     // Trim trailing spaces
    while (len > 0 && buffer[len - 1] == ' ')
        buffer[--len] = '\0';    
    if (len > 10)  return NULL;      // introduce leak

    char *trimmed = malloc(len + 1);
    if (!trimmed) return NULL;
    strcpy(trimmed, buffer);
    free(buffer);
    return trimmed;
}

int main(void) {
    const char *inputs[] = {
        "short   ",
        "this input is definitely too long---",
        "fine  ",
        NULL
    };

    for (int i = 0; inputs[i]; i++) {
        char *out = duplicate_and_trim(inputs[i]);
        if (!out) {
            fprintf(stderr, "[!] failed to process \"%s\", leak may have occurred\n", inputs[i]);
            continue;
        }
        printf("-> “%s”\n", out);
        free(out);
    }

    return 0;
}
