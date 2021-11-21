import os

LS_COLORS = {
  (k:=entry.partition('='))[0].replace('*','') : k[2]
  for entry in os.getenv('LS_COLORS','').split(':')[:-1]
}

print(LS_COLORS)

"""
fi  FILE  Normal file
di  DIR Directory
ln  SYMLINK, LINK, LNK  Symbolic link. If you set this to 'target' instead of a numerical value, the colour is as for the file pointed to.
pi  FIFO, PIPE  Named pipe
do  DOOR  Door
bd  BLOCK, BLK  Block device
cd  CHAR, CHR Character device
or  ORPHAN  Symbolic link pointing to a non-existent file
so  SOCK  Socket
su  SETUID  File that is setuid (u+s)
sg  SETGID  File that is setgid (g+s)
tw  STICKY_OTHER_WRITABLE Directory that is sticky and other-writable (+t,o+w)
ow  OTHER_WRITABLE  Directory that is other-writable (o+w) and not sticky
st  STICKY  Directory with the sticky bit set (+t) and not other-writable
ex  EXEC  Executable file (i.e. has 'x' set in permissions)
mi  MISSING Non-existent file pointed to by a symbolic link (visible when you type ls -l)
lc  LEFTCODE, LEFT  Opening terminal code
rc  RIGHTCODE, RIGHT  Closing terminal code
ec  ENDCODE, END  Non-filename text
*.extension   Every file using this extension e.g. *.jpg
"""