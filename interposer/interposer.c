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
#include <stdlib.h>
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


void gtk_window_set_title(GtkWindow *window, const gchar *title)
{
 static void (*next_func)(GtkWindow *window, const gchar *title)=NULL;

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


void gtk_window_set_modal(GtkWindow* window, gboolean modal)
{
 static void (*next_func)(GtkWindow* window, gboolean modal)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping set modal\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_modal");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window, modal);
 printf("GTK:Window Set Modal:%s %d\n", gtk_window_get_title(window), modal);
 fflush(stdout);
}


void gtk_widget_show(GtkWidget* widget)
{
 static void (*next_func)(GtkWidget* widget)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping widget show\n");
    next_func=dlsym(RTLD_NEXT,"gtk_widget_show");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(widget);
 if (GTK_IS_WINDOW(widget))
    printf("GTK:Window Show:%s\n", gtk_window_get_title(GTK_WINDOW(widget)));
 /*else
    printf("GTK:Window Show:Widget:%s\n", gtk_widget_get_name(widget));*/
 fflush(stdout);
}


void gtk_button_set_label(GtkButton* button, const char *label)
{
 static void (*next_func)(GtkButton* button, const char *label)=NULL;
 const char *ori=label;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping button label\n");
    next_func=dlsym(RTLD_NEXT,"gtk_button_set_label");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 if (g_strcmp0(label, "Print")==0)
    /* Why KiCad people hates shortcuts? */
    label="_Print";
 else if (label[0]=='S' && label[1]=='a' && label[2]=='v' && label[3]=='e')
    label="_Save";
 next_func(button, label);
 printf("GTK:Button Label:%s\n", label);
 if (label!=ori)
    printf("GTK:Button Label:**Changed from %s\n", ori);
 fflush(stdout);
}

gchar *dir_name="/tmp";
gchar *base_name="pp";
gchar *format="pdf";

/*
  Loads the print options from a file named "interposer_options.txt". I.e:
/tmp
pp
pdf
*/
void load_print_options()
{
 GIOChannel *f;
 gchar *line;
 gsize length, terminator_pos;
 char *fn;

 fn=getenv("KIAUTO_INTERPOSER_PRINT");
 if (fn==NULL)
   {
    printf("GTK:Error:KIAUTO_INTERPOSER_PRINT not defined\n");
    return;
   }
 printf("GTK:Read:Dir_Name:%s\n", dir_name);
 f=g_io_channel_new_file(fn, "r", NULL);
 if (f==NULL)
   {
    printf("GTK:Error:Unable to load %s\n", fn);
    return;
   }
 g_io_channel_read_line(f, &dir_name, &length, &terminator_pos, NULL);
 dir_name[terminator_pos]=0;
 printf("GTK:Read:Dir_Name:%s\n", dir_name);
 g_io_channel_read_line(f, &base_name, &length, &terminator_pos, NULL);
 base_name[terminator_pos]=0;
 printf("GTK:Read:Base_Name:%s\n", base_name);
 g_io_channel_read_line(f, &format, &length, &terminator_pos, NULL);
 format[terminator_pos]=0;
 printf("GTK:Read:Format:%s\n", format);
 g_io_channel_unref(f);
}


/*
  Forces the GTK print dialog to select the output file, format and printer we want
*/
GtkPrintOperationResult gtk_print_operation_run(GtkPrintOperation* op, GtkPrintOperationAction action, GtkWindow* parent, GError** error)
{
 static GtkPrintOperationResult (*next_func)(GtkPrintOperation* , GtkPrintOperationAction , GtkWindow* , GError** )=NULL;
 GtkPrintOperationResult res;
 GtkPrintSettings *print_sets;
 GtkSettings *gtk_sets;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping print op run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_print_operation_run");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
    load_print_options();
   }

 print_sets = gtk_print_operation_get_print_settings(op);
 /* Select the file format and name */
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_BASENAME, base_name);
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_DIR, dir_name);
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_FILE_FORMAT, format);
 /* Choose the "Print to File" printer */
 gtk_print_settings_set_printer(print_sets, "Print to File");
 /* Restrict the backends to "file", otherwise the default printer will prevail */
 gtk_sets = gtk_settings_get_default();
 g_object_set(gtk_sets, "gtk-print-backends", "file", NULL);

 /* Now run the dialog. Lamentably GTK_PRINT_OPERATION_ACTION_PRINT can't be used. IMHO a bug */
 res = next_func(op, action, parent, error);
 printf("GTK:Print Run:%s\n", gtk_window_get_title(parent));

 fflush(stdout);
 return res;
}


void gtk_label_set_text_with_mnemonic(GtkLabel *label, const gchar *str)
{
 static void (*next_func)(GtkLabel *label, const gchar *str)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping label set text\n");
    next_func=dlsym(RTLD_NEXT,"gtk_label_set_text_with_mnemonic");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 if (g_strcmp0(str, "Report all errors for tracks (slower)")==0)
    str="_Report all errors for tracks (slower)";
 next_func(label, str);

 printf("GTK:Label Set Text 2:%s\n", str);
 fflush(stdout);
}

