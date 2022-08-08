#!/usr/bin/perl
$c=1;
while (<>)
  {
   if ($_=~/(GTK:Window|GTK:Main|DEBUG:=|INFO:|DEBUG:Waiting for \`\[\'IO:|DEBUG:\['xdotool', '(key|click)',|Interposer match|DEBUG:Found IO)/)  # "\* "
     {
      if ($_=~/(INFO:)/)
        {
         print("\n");
        }
      printf("%05d %s", $c, $_);
     }
   $c++;
  }
