#include "s3common_writer.h"
#include "s3macros.h"

void S3CommonWriter::open(const WriterParams& params) {
    this->keyWriter.setS3interface(this->s3service);

    if (s3ext_autocompress) {
        this->upstreamWriter = &this->compressWriter;
        this->compressWriter.setWriter(&this->keyWriter);
    } else {
        this->upstreamWriter = &this->keyWriter;
    }

    this->upstreamWriter->open(params);
}

uint64_t S3CommonWriter::write(const char* buf, uint64_t count) {
    return this->upstreamWriter->write(buf, count);
}

void S3CommonWriter::close() {
    this->upstreamWriter->close();
}