StatMask2FileType = {
    0x8000: "file",
    0x4000: "directory",
    0x2000: "chardevice",
    0x6000: "blockdevice",
    0x1000: "fifo",
    0xa000: "symlink",
    0xc000: "socket",
}

def filetype(pathobj):
    return StatMask2FileType.get(pathobj.lstat().st_mode & 0xf000, 'file')