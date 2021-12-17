import pathlib
from enum import Enum, auto

class FileType(Enum):
    FILE        = auto()
    DIRECTORY   = auto()
    CHARDEVICE  = auto()
    BLOCKDEVICE = auto()
    FIFO        = auto()
    SYMLINK     = auto()
    SOCKET      = auto()


StatMask2FileType = {
    0x4000: FileType.DIRECTORY,
    0x2000: FileType.CHARDEVICE,
    0x6000: FileType.BLOCKDEVICE,
    0x8000: FileType.FILE,
    0x1000: FileType.FIFO,
    0xa000: FileType.SYMLINK,
    0xc000: FileType.SOCKET,
}


def filetype(pathlike: pathlib.Path):
    mode = pathlike.lstat().st_mode
    mask =  mode & 0xf000
    return StatMask2FileType.get(mask, FileType.FILE)