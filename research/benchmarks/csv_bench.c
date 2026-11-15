#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>
#include "csv.h"
typedef struct {unsigned char *data;size_t n;} field;
static field fields[4096];static size_t nf=0;
static void collect(void *s,size_t n,void *ctx) {
    (void)ctx;if(nf==4096)abort();
    fields[nf].data=malloc(n+1);if(!fields[nf].data)abort();
    if(n)memcpy(fields[nf].data,s,n);fields[nf++].n=n;
}
static double seconds(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+1e-9*t.tv_nsec;}
static volatile uint64_t sink;
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    size_t n=0;int mode=1;unsigned char quote='"';
    if(!strcmp(argv[1],"count1024")){n=1024;mode=0;}
    else if(!strcmp(argv[1],"sized1024")){n=1024;}
    else if(!strcmp(argv[1],"sized32")){n=32;}
    else if(!strcmp(argv[1],"count5553")){n=5553;mode=0;}
    else if(!strcmp(argv[1],"quoted")){n=2048;}
    else if(!strcmp(argv[1],"direct256")){n=256;mode=2;}
    else if(!strcmp(argv[1],"metadata")){mode=3;}
    else if(!strcmp(argv[1],"custom255")){n=521;quote=255;}
    else return 2;
    if(mode==3) {
        FILE *f=fopen(CORPUS_PATH,"rb");if(!f)return 3;
        struct csv_parser parser;csv_init(&parser,CSV_STRICT);
        char buf[4096];size_t got;
        while((got=fread(buf,1,sizeof(buf),f)))if(csv_parse(&parser,buf,got,collect,NULL,NULL)!=got)return 3;
        if(csv_fini(&parser,collect,NULL,NULL))return 3;
        csv_free(&parser);fclose(f);mode=1;
    } else {
        unsigned char *buf=malloc(n);if(!buf)return 3;
        for(size_t i=0;i<n;i++)buf[i]=(unsigned char)('a'+i%26);
        if(!strcmp(argv[1],"quoted"))for(size_t i=0;i<n;i+=7)buf[i]=quote;
        if(quote==255)for(size_t i=0;i<n;i+=31)buf[i]=quote;
        collect(buf,n,NULL);free(buf);
    }
    size_t total=0,maxn=0;uint64_t h=0;
    for(size_t i=0;i<nf;i++){total+=fields[i].n;if(fields[i].n>maxn)maxn=fields[i].n;}
    unsigned char *out=malloc(maxn*2+2);if(!out)return 3;
    for(size_t i=0;i<nf;i++) {
        size_t len=csv_write2(out,maxn*2+2,fields[i].data,fields[i].n,quote);
        for(size_t j=0;j<len;j++)h=h*33+out[j];
    }
    if(!total)return 3;
    size_t loops=(64u*1024u*1024u)/total;if(loops<1000)loops=1000;
    uint64_t check=0;double start=seconds();
    for(size_t k=0;k<loops;k++)for(size_t i=0;i<nf;i++) {
        field f=fields[i];
        if(mode==0)check+=csv_write2(NULL,0,f.data,f.n,quote);
        else if(mode==1) {
            size_t need=csv_write2(NULL,0,f.data,f.n,quote);
            check+=csv_write2(out,need,f.data,f.n,quote)+out[need-1];
        } else check+=csv_write2(out,maxn*2+2,f.data,f.n,quote)+out[0];
    }
    double elapsed=seconds()-start;sink=check;
    struct rusage usage;getrusage(RUSAGE_SELF,&usage);
    printf("{\"seconds\":%.9f,\"checksum\":\"%llu:%llu\",\"peak_rss_kb\":%ld,\"input_bytes_per_batch\":%zu,\"batches\":%zu}\n",elapsed,(unsigned long long)h,(unsigned long long)check,usage.ru_maxrss,total,loops);
    for(size_t i=0;i<nf;i++)free(fields[i].data);free(out);return 0;
}
