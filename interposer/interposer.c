/****************************************************************************
 -*- coding: utf-8 -*-
 Copyright (c) 2022 Salvador E. Tropea
 Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
 License: GPLv3+
 Project: KiAuto (formerly kicad-automation-scripts)
 Description:
 This module implements "Function Interposition" to determine what's KiCad
 doing. The main motivation is to reduce time-out problems in the 3D
 renderer.
****************************************************************************/

#include <stdio.h>
#include <dlfcn.h> /* header required for dlsym() */
#include <string.h>
#include <pango/pango.h>
#include <GL/glx.h>
#include <gtk/gtk.h>

void glXSwapBuffers(Display *dpy, GLXDrawable drawable)
{
 static void (*next_func)(Display *, GLXDrawable)=NULL;
 static int cnt=0;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping GLX\n");
    next_func=dlsym(RTLD_NEXT,"glXSwapBuffers");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(dpy, drawable);
 printf("GLX:Swap %d\n", cnt++);
 fflush(stdout);
}

#define MAX_STORE 1024

void pango_layout_set_text(PangoLayout *layout, const char *text, int length)
{
 static void (*next_func)(PangoLayout *, const char *, int)=NULL;
 static char buffer[MAX_STORE];

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping PANGO\n");
    next_func=dlsym(RTLD_NEXT,"pango_layout_set_text");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
    buffer[0]=0;
   }

 /* Filter what we log */
 if (text[0]!=0 &&  /* Emty strings??!! */
     !(text[0]=='g' && text[1]==0) &&   /* g seems to be used to meassure */
     !(text[0]=='.' && text[1]=='.' && text[2]=='.' && text[3]==0) &&
     strcmp(text, "ABCDEFHXfgkj"))  /* To meassure? */
   {/* Avoid repetition */
    if (strncmp(text, buffer, MAX_STORE))
       printf("PANGO:%s\n", text); /* Most stuff is sent 3 times!!! */
       fflush(stdout);
    strncpy(buffer, text, MAX_STORE);
   }
 return next_func(layout, text, length);
}


GtkWidget *gtk_scrolled_window_new(GtkAdjustment *hadjustment, GtkAdjustment *vadjustment)
{
 static GtkWidget *(*next_func)(GtkAdjustment *, GtkAdjustment *)=NULL;
 GtkWidget *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping window creation\n");
    next_func=dlsym(RTLD_NEXT,"gtk_scrolled_window_new");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res=next_func(hadjustment, vadjustment);
 printf("GTK:Window_Creation\n");
 fflush(stdout);

 return res;
}


void gtk_window_set_title(GtkWindow *window, const gchar *title)
{
 static GtkWidget *(*next_func)(GtkWindow *window, const gchar *title)=NULL;
 GtkWidget *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping window title change\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_title");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window, title);
 printf("GTK:Window Title:%s\n", title);
 fflush(stdout);
}
