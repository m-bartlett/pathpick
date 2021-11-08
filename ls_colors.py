import os

LS_COLORS = {
  (k:=entry.partition('='))[0].replace('*','') : k[2]
  for entry in os.getenv('LS_COLORS','').split(':')[:-1]
}

print(LS_COLORS)