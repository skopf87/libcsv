#define _GNU_SOURCE
#include <sys/mman.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "csv.h"
int main(void) {
    size_t p=(size_t)sysconf(_SC_PAGESIZE);
    char *mem=mmap(NULL,4*p,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(mem!=MAP_FAILED);assert(mprotect(mem+p,p,PROT_NONE)==0);assert(mprotect(mem+3*p,p,PROT_NONE)==0);
    for(size_t n=0;n<1024;n++) {
        char *s=mem+p-n;memset(s,'a',n);
        char *d=mem+3*p-(n+2);
        assert(csv_write2(NULL,0,s,n,'"')==n+2);
        assert(csv_write2(d,n+2,s,n,'"')==n+2);
        assert(d[0]=='"'&&d[n+1]=='"');
        if(n) {s[n-1]='"';assert(csv_write2(NULL,0,s,n,'"')==n+3);}
    }
    munmap(mem,4*p);puts("4095 protected-page serialization checks passed");return 0;
}
