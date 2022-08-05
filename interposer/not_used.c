Random pieces of code used for the interposer during tests.

    GtkPageOrientation orie=gtk_print_settings_get_orientation(set);
    printf("GTK:Paper orientation: ");
    if (orie==GTK_PAGE_ORIENTATION_PORTRAIT)
       printf("Portrait\n");
    else if (orie==GTK_PAGE_ORIENTATION_LANDSCAPE)
       printf("Landscape\n");
    else if (orie==GTK_PAGE_ORIENTATION_REVERSE_PORTRAIT)
       printf("Reverse Portrait\n");
    else if (orie==GTK_PAGE_ORIENTATION_REVERSE_LANDSCAPE)
       printf("Reverse Landscape\n");


 printf("GTK:Print Run:Before calling\n");
 set = gtk_print_operation_get_print_settings(op);
 if (set)
   {
    gtk_print_settings_set_orientation(set, GTK_PAGE_ORIENTATION_LANDSCAPE);
    printf("GTK:Printer:%s\n", gtk_print_settings_get_printer(set));
    gtk_print_settings_foreach(set, pr_setting, NULL);
    gtk_print_settings_set_printer(set, "");
   }


 // Old mechanism
 //gtk_print_settings_set_print_to_file(set, True);
 //gtk_print_settings_set(set, GTK_PRINT_SETTINGS_PRINT_TO_FILE , "True");

 printf("---\n");
 set = gtk_print_operation_get_print_settings(op);
 gtk_print_settings_foreach(set, pr_setting, NULL);
 printf("---\n");

 //action = GTK_PRINT_OPERATION_ACTION_EXPORT;
 //action = GTK_PRINT_OPERATION_ACTION_PRINT;

 set = gtk_print_operation_get_print_settings(op);
 gtk_print_settings_foreach(set, pr_setting, NULL);


void pr_setting(const gchar* key, const gchar* value, gpointer user_data)
{
 printf("GTK:Print Setting:%s='%s'\n", key, value);
}

void gtk_window_set_hide_on_close(GtkWindow* window, gboolean modal)
{
 static void (*next_func)(GtkWindow* window, gboolean modal)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_hide_on_close");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window, modal);
 printf("GTK:Window Set Hide on Close:%s %d\n", gtk_window_get_title(window), modal);
 fflush(stdout);
}


void gtk_window_present(GtkWindow* window)
{
 static void (*next_func)(GtkWindow*)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_present");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window);
 printf("GTK:Window Present:%s\n", gtk_window_get_title(window));
 fflush(stdout);
}


void gtk_window_set_focus(GtkWindow* window, GtkWidget* focus)
{
 static void (*next_func)(GtkWindow*, GtkWidget*)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_focus");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window, focus);
 printf("GTK:Window Set Focus:%s\n", gtk_window_get_title(window));
 fflush(stdout);
}

void gtk_window_destroy(GtkWindow* window)
{
 static void (*next_func)(GtkWindow*)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_destroy");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window);
 printf("GTK:Window Destroy:%s\n", gtk_window_get_title(window));
 fflush(stdout);
}


void gtk_window_close(GtkWindow* window)
{
 static void (*next_func)(GtkWindow*)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_close");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 next_func(window);
 printf("GTK:Window Close:%s\n", gtk_window_get_title(window));
 fflush(stdout);
}


gint gtk_dialog_run(GtkDialog* dialog)
{
 static gint (*next_func)(GtkDialog* dialog)=NULL;
 gint res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping dialog run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_dialog_run");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res = next_func(dialog);
 printf("GTK:Dialog Run:%s\n", gtk_window_get_title(GTK_WINDOW(dialog)));
 fflush(stdout);
 return res;
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


GtkWidget *gtk_radio_button_new_with_label(GSList *group, const gchar *label)
{
 static GtkWidget *(*next_func)(GSList *group, const gchar *label)=NULL;
 GtkWidget *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping radio label\n");
    next_func=dlsym(RTLD_NEXT,"gtk_radio_button_new_with_label");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res = next_func(group, label);
 printf("GTK:Radio Button Label:%s\n", label);
 fflush(stdout);

 return res;
}


GtkWidget *gtk_radio_button_new_with_mnemonic(GSList *group, const gchar *label)
{
 static GtkWidget *(*next_func)(GSList *group, const gchar *label)=NULL;
 GtkWidget *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping radio label 2\n");
    next_func=dlsym(RTLD_NEXT,"gtk_radio_button_new_with_mnemonic");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res = next_func(group, label);
 printf("GTK:Radio Button Label 2:%s\n", label);
 fflush(stdout);

 return res;
}


void gtk_label_set_text(GtkLabel *label, const gchar *str)
{
 static void (*next_func)(GtkLabel *label, const gchar *str)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping label set text\n");
    next_func=dlsym(RTLD_NEXT,"gtk_label_set_text");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 if (g_strcmp0(str, "Report all errors for tracks (slower)")==0)
    str="_Report all errors for tracks (slower)";
 next_func(label, str);

 printf("GTK:Label Set Text:%s\n", str);
 fflush(stdout);
}


int open(const char *pathname, int flags, mode_t mode)
{
 static int (*next_func)(const char *, int , mode_t)=NULL;
 int res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping open\n");
    next_func=dlsym(RTLD_NEXT,"open");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res=next_func(pathname, flags, mode);

 printf("IO:open:%s\n", pathname);
 fflush(stdout);
 return res;
}


int creat(const char *pathname, mode_t mode)
{
 static int (*next_func)(const char *, int)=NULL;
 int res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping creat\n");
    next_func=dlsym(RTLD_NEXT,"creat");
    if ((msg=dlerror())!=NULL)
       printf("** dlopen failed : %s\n", msg);
   }

 res=next_func(pathname, mode);

 printf("IO:creat:%s\n", pathname);
 fflush(stdout);
 return res;
}



