/*
 * tazpkg-notification: part of TazPkg - SliTaz package manager.
 * Show Freedesktop notification (with action buttons).
 *
 * Based on the sources provided in the libnotify / tests.
 * Copyright(C) 2004 Mike Hearn <mike@navi.cx> - LGPL 2.1
 *
 * I have no skills in C. This program may have bugs.
 * Aleksej Bobylev <al.bobylev@gmail.com>, 2016
 *
 * Commandline arguments:
 *   1 : Notification body text
 *  [2]: Urgency flag:
 *       0 or absent: normal urgency
 *       1: critical urgency
 *  [3]: Button label for first action
 *  [4]: Button label for second action
 *
 * Output:
 *   1: If first button was pressed
 *   2: If second button was pressed
 */

#include <libnotify/notify.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

static GMainLoop *loop;

static void
_handle_closed (GObject * obj)
{
	printf ("\n");
	g_object_unref (obj);
	g_main_loop_quit (loop);
}

static void
action1_callback (NotifyNotification *n, const char *action)
{
	g_assert (action != NULL);
	g_assert (strcmp (action, "act1") == 0);

	printf ("1");

	notify_notification_close (n, NULL);

	g_main_loop_quit (loop);
}
static void
action2_callback (NotifyNotification *n, const char *action)
{
	g_assert (action != NULL);
	g_assert (strcmp (action, "act2") == 0);

	printf ("2");

	notify_notification_close (n, NULL);

	g_main_loop_quit (loop);
}


int
main (int argc, char **argv)
{
	NotifyNotification *n;

	if (!notify_init ("TazPkg Notification"))
		exit (1);

	loop = g_main_loop_new (NULL, FALSE);

	if (argc < 3 || strcmp (argv[2], "0") == 0) {
		n = notify_notification_new ("TazPkg", argv[1], "dialog-information");
	} else {
		n = notify_notification_new ("TazPkg", argv[1], "dialog-warning");
		notify_notification_set_urgency (n, NOTIFY_URGENCY_CRITICAL);
		notify_notification_set_timeout (n, NOTIFY_EXPIRES_NEVER);
	}

	notify_notification_set_hint (n, "transient", g_variant_new_boolean (TRUE));

	if (argc >= 4)
		notify_notification_add_action (n, "act1", argv[3], (NotifyActionCallback) action1_callback, NULL, NULL);
	if (argc >= 5)
		notify_notification_add_action (n, "act2", argv[4], (NotifyActionCallback) action2_callback, NULL, NULL);

	g_signal_connect (G_OBJECT (n), "closed", G_CALLBACK (_handle_closed), NULL);

	if (!notify_notification_show (n, NULL))
		return 1;

	g_main_loop_run (loop);

	return 0;
}
