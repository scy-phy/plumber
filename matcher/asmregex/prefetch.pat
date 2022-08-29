[prefetch]
# Match an ARM load instruction (ARMLD) with operands:
# Op. 0: AG: A register name.
# Op. 1: QR: '[', followed by a register name.
# Op. 2: RO: A register name, optionally followed by ']'.
# Store (*) the value of capture group 1 in Op. 1 (i.e.,
# the name of the base register) in backref. base_reg.
<ARMLD,AG,QR,RO,{1:1:*base_reg}>
<any,>{0,5}                # 0 to 5 arbitrary instructions
# Another load, Op. 1 must match (=) the base_reg backref.
<ARMLD,AG,QR,RO,{1:1:=base_reg}>
<any,>{0,5}                # 0 to 5 arbitrary instructions
<ARMLD,AG,QR,RO,{1:1:=base_reg}>            # Another load
