#!/bin/sh
# Runs KiCad with the interposer enabled
# We use LANG=C to avoid translations, this works on Debian 11
#LANG=C LD_PRELOAD=`pwd`/libinterposer.so eeschema "$@" | grep "GTK:"
#LANG=C LD_PRELOAD=`pwd`/libinterposer.so eeschema "$@"
LANG=C LD_PRELOAD=`pwd`/libinterposer.so pcbnew "$@" | grep "GTK:Main"
#LANG=C LD_PRELOAD=`pwd`/libinterposer.so pcbnew "$@"
