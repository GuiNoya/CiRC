#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""run_this_first.py - CiRC MIME register

Script to register MIME types of the compressed
and comic books files, so that the dialogs can
filter the results.
Actually it works with Windows and Linux.
If someone on another system can help, please contact me.
Contact me if you find a bug too.

Note: This script only register MIME types, it don't bind the
      files with CiRC. I don't know if I will do this later.

Note 2: Actually the program and the files don't have any icon.
        If you want to do them, do it and send to me, then will
        put it in the files. Do the icons on the following
        resolutions: 16x16, 22x22, 24x24, 32x32, 48x48 or send me
        a scalable file. =D

By: Guilherme Pereira Noya
<gui_noya@hotmail.com>
<gui.noya@gmail.com>"""

import os
import sys
import subprocess

def register_mime_types_for_linux():
    """Install the MIME types of the .cbz .cbr .cbt .cb7 on linux systems."""
    if not os.path.isfile(os.path.dirname(__file__) + os.sep + 'circ.xml'):
        print("Error! circ.xml not found!\n")
        print("Please verify keep circ.xml an this file together.\n")
        print("If they are together, send me a bug report to:\n")
        print("<gui_noya@hotmail.com>\n<gui.noya@gmail.com>")
    else:
        try:
            retcode = subprocess.call('xdg-mime install --novendor circ.xml', shell=True)
            if retcode == 0:
                print("\nInstallation Sucessfull.")
                print("Now you can start CiRC, and don't need to run this script anymore.")
            elif retcode == 1:
                print("\n\nInstallation failed! Probally this is a bug or an error that I made, " +
                "please send me a bug report with what showed up in terminal." +
                "e-mails:\n<gui_noya@hotmail.com>\n<gui.noya@gmail.com")
            elif retcode == 3 or retcode == 4:
                print("\n\nInstallation failed! Generic error. Sorry.")
            elif retcode == 5:
                print("\n\nInstallation failed! You don't have the right permissions to install" +
                " the MIME types, check if the circ.xml have the permission to be read.")
        except OSError as error:
            print("\n\nInstallation failed: " + error)

def register_mime_types_for_win32():
    """Register the MIME types to the especified files
in the Windows. Meh. That was easy, it's a joke to
play with the Windows registry."""
    failed = []
    reg_list = []
    parent_path_key = r"Software\Classes"
    reg_list.append((r"\.zip", r'application/zip'))
    reg_list.append((r"\.rar", r'application/x-rar'))
    reg_list.append((r"\.7z", r'application/x-7z-compressed'))
    reg_list.append((r"\.tar", r'application/x-tar'))
    reg_list.append((r"\.bz2", r'application/x-bzip2'))
    reg_list.append((r"\.gz", r'application/x-gzip'))
    reg_list.append((r"\.cbr", r'application/x-cbr'))
    reg_list.append((r"\.cbz", r'application/x-cbz'))
    reg_list.append((r"\.cbt", r'application/x-cbt'))
    reg_list.append((r"\.cb7", r'application/x-cb7'))
    for (extension, mime) in reg_list:
        print("Registering " + extension[2:] + " ...")
        try:
            try:
                key = OpenKey(HKEY_LOCAL_MACHINE, parent_path_key+extension, 0, KEY_ALL_ACCESS)
            except:
                key = CreateKey(HKEY_LOCAL_MACHINE, parent_path_key+extension)
            SetValueEx(key, "Content Type", 0, REG_SZ, mime)
        except:
            print("Failed registring " + extension[2:] + " MIME Type...")
            failed.append(extension[2:])
    if not failed:
        print("\nAll MIME types registered sucessfully." +
            "\nNow you can start CiRC, and don't need to run this " +
            "script again!")
    else:
        print("\nThe following files MIME types couldn't be registered:\n")
        for type in failed:
            print(type + "\n")
        print("Maybe when you try to filter files in dialogs, the files will not show" +
        " or will be bugged.\nTry to run this script again, be sure to run as admin.")

if __name__ == "__main__":
    if (os.name == "nt") and (sys.platform == "win32"):
        print("Registering MIME Types for Windows.\n")
        print("Please Wait...\n")
        try:
            from _winreg import *
            register_mime_types_for_win32()
        except:
            pass
    elif (os.name == "posix") and (sys.platform == "linux2"):
        print("Registering MIME Types for Linux.\n")
        print("Please Wait...\n")
        register_mime_types_for_linux()
    elif os.name in ("os2", "ce", "riscos"):
        print("I haven't done a register for your system. Sorry!\n")
        print("If you have some knowledge about registering" +
            "something in your system, you can help to make this register." +
            "Please, contact me:\ngui_noya@hotmail.com\ngui.noya@gmail.com")
    else:
        print("Sorry, can't identify your SO.")