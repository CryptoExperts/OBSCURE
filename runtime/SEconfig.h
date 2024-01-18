#ifndef SECONFIG_H
#define SECONFIG_H

#define VERSION               0
#define WORD_SIZE             32

#define SE_TINY       0
#define SE_SMALL      0
#define SE_MEDIUM     1
#define SE_LARGE      0
#define SE_EXTRALARGE 0

#if defined(SE_TINY) && (SE_TINY)
#define LLMI_MAX_INPUT_COUNT  2         // l_in
#define LLMI_MAX_OUTPUT_COUNT 2         // l_out
#define REGISTER_COUNT        6        // r
#define LLS_MAX_LENGTH        2         // s
#elif defined(SE_SMALL) && (SE_SMALL)
#define LLMI_MAX_INPUT_COUNT  8         // l_in
#define LLMI_MAX_OUTPUT_COUNT 8         // l_out
#define REGISTER_COUNT        40        // r
#define LLS_MAX_LENGTH        32        // s
#elif defined(SE_MEDIUM) && (SE_MEDIUM)
#define LLMI_MAX_INPUT_COUNT  16        // l_in
#define LLMI_MAX_OUTPUT_COUNT 16        // l_out
#define REGISTER_COUNT        80        // r
#define LLS_MAX_LENGTH        64        // s
#elif defined(SE_LARGE) && (SE_LARGE)
#define LLMI_MAX_INPUT_COUNT  32        // l_in
#define LLMI_MAX_OUTPUT_COUNT 32        // l_out
#define REGISTER_COUNT        160        // r
#define LLS_MAX_LENGTH        128        // s
#elif defined(SE_EXTRALARGE) && (SE_EXTRALARGE)
#define LLMI_MAX_INPUT_COUNT  64        // l_in
#define LLMI_MAX_OUTPUT_COUNT 64        // l_out
#define REGISTER_COUNT        320        // r
#define LLS_MAX_LENGTH        256        // s
#else // my config
#define LLMI_MAX_INPUT_COUNT  16         // l_in
#define LLMI_MAX_OUTPUT_COUNT 16         // l_out
#define REGISTER_COUNT        48         // r
#define LLS_MAX_LENGTH        20         // s
#endif

#define l_out LLMI_MAX_OUTPUT_COUNT

// SE is planned to support u32 and u64
#if defined(WORD_SIZE) && (WORD_SIZE == 64)
  typedef unsigned long long uSE;
#else
  typedef unsigned int uSE;
#endif

#endif