class Style():
  prefix     = ''
  foreground = None
  background = None
  bold       = False
  italic     = False
  underline  = False
  reverse    = False
  reset      = True
  suffix     = ''
  template   = '{}'
  length     = 0
  prefix_length = 0
  suffix_length = 0


  def __init__( self,
                prefix     = '',
                foreground = None,
                background = None,
                bold       = False,
                italic     = False,
                underline  = False,
                reverse    = False,
                reset      = True,
                suffix     = '', **kwargs ):
    self.prefix     = prefix
    self.foreground = foreground
    self.background = background
    self.bold       = bold
    self.italic     = italic
    self.underline  = underline
    self.reverse    = reverse
    self.reset      = reset
    self.suffix     = suffix
    self.update_template()


  def update_template(self):
    ANSI_sequence = []
    format_placeholder = '{}'
    if self.foreground is not None: ANSI_sequence.append(f"3{self.foreground}")
    if self.background is not None: ANSI_sequence.append(f"4{self.background}")
    if self.bold:                   ANSI_sequence.append("1")
    if self.italic:                 ANSI_sequence.append("3")
    if self.underline:              ANSI_sequence.append("4")
    if self.reverse:                ANSI_sequence.append("7")
    if ANSI_sequence:               ANSI_sequence = f"\033[{';'.join(ANSI_sequence)}m"
    else:                           ANSI_sequence=''
    if self.reset:                  format_placeholder += "\033[0m"
    self.template = f"{self.prefix}{ANSI_sequence}{format_placeholder}{self.suffix}"
    self.suffix_length = len(self.suffix)
    self.prefix_length = len(self.prefix)
    self.length = self.suffix_length + self.prefix_length


  def format(self, text):
    return self.template.format(text)


  def apply(self, other):
    self.prefix = other.prefix + self.prefix
    self.suffix = other.suffix + self.suffix
    self.foreground = (
      getattr(other, "foreground", None) or getattr(self, "foreground", None)
    )
    self.background = (
      getattr(other, "background", None) or getattr(self, "background", None)
    )
    self.update_template()


  def __repr__(self):
    return str(self.__dict__)


  def __len__(self):
    return self.length