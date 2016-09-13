#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>

#include <map>
#include <string>

#include "http_parser.h"

#include "s3log.h"
#include "s3macros.h"
#include "s3url.h"
#include "s3utils.h"

using std::string;
using std::stringstream;

UrlParser::UrlParser(const string &url) {
    CHECK_ARG_OR_DIE(!url.empty());

    this->fullurl = url;

    struct http_parser_url url_parser;
    int result =
        http_parser_parse_url(this->fullurl.c_str(), this->fullurl.length(), false, &url_parser);
    CHECK_OR_DIE_MSG(result == 0, "Failed to parse URL %s at field %d", this->fullurl.c_str(),
                     result);

    this->schema = extractField(&url_parser, UF_SCHEMA);
    this->host = extractField(&url_parser, UF_HOST);
    this->path = extractField(&url_parser, UF_PATH);
    this->query = extractField(&url_parser, UF_QUERY);
}

string UrlParser::extractField(const struct http_parser_url *url_parser, http_parser_url_fields i) {
    if ((url_parser->field_set & (1 << i)) == 0) {
        return "";
    }

    return this->fullurl.substr(url_parser->field_data[i].off, url_parser->field_data[i].len);
}

string S3UrlUtility::replaceSchemaFromURL(const string &url, bool useHttps) {
    size_t iend = url.find("://");
    if (iend == string::npos) {
        return url;
    }

    return getDefaultSchema(useHttps) + url.substr(iend);
}

string S3UrlUtility::getDefaultSchema(bool useHttps) {
    return useHttps ? "https" : "http";
}

// Set AWS region, use 'external-1' if it is 'us-east-1' or not present
// http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
string S3UrlUtility::getRegionFromURL(const string &url) {
    size_t ibegin =
        url.find("://s3") + strlen("://s3");  // index of character('.' or '-') after "3"
    size_t iend = url.find(".amazonaws.com");

    string region;
    if (iend == string::npos) {
        return region;
    } else if (ibegin == iend) {  // "s3.amazonaws.com"
        return "external-1";
    } else {
        // ibegin + 1 is the character after "s3." or "s3-"
        // for instance: s3-us-west-2.amazonaws.com
        region = url.substr(ibegin + 1, iend - (ibegin + 1));
    }

    if (region.compare("us-east-1") == 0) {
        region = "external-1";
    }
    return region;
}

string S3UrlUtility::getBucketFromURL(const string &url) {
    size_t ibegin = find_Nth(url, 3, "/");
    size_t iend = find_Nth(url, 4, "/");
    if (ibegin == string::npos) {
        return string();
    }
    // s3://s3-region.amazonaws.com/bucket
    if (iend == string::npos) {
        return url.substr(ibegin + 1, url.length() - ibegin - 1);
    }

    return url.substr(ibegin + 1, iend - ibegin - 1);
}

string S3UrlUtility::getPrefixFromURL(const string &url) {
    size_t ibegin = find_Nth(url, 3, "/");
    size_t iend = find_Nth(url, 4, "/");

    // s3://s3-region.amazonaws.com/bucket
    if (ibegin == string::npos || iend == string::npos) {
        return string();
    }

    // s3://s3-region.amazonaws.com/bucket/
    if (iend == url.length() - 1) {
        return string();
    }

    ibegin = find_Nth(url, 4, "/");
    // s3://s3-region.amazonaws.com/bucket/prefix
    // s3://s3-region.amazonaws.com/bucket/prefix/whatever
    return url.substr(ibegin + 1, url.length() - ibegin - 1);
}
