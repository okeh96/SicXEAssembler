##############################################################################
###                                                                        ###
### assem.py                                                               ###
###                                                                        ###
### Author: Oliver Keh                                                     ###
###                                                                        ###
### Date: 12/11/2016                                                       ###
###                                                                        ###
### This program reads and assembles a SIC/XE assembly program that        ###
### supports all mnemonics and addressing modes. The program outputs an    ###
### annotated source code listing and writes the assembled bytes of the    ###
### program to a new file, <filename>.exe.                                 ###
###                                                                        ###
##############################################################################

import sys
import io

OPTAB = {'ADD':'18', 'ADDF':'58', 'ADDR':'90', 'AND':'40', 'CLEAR':'B4', 
           'COMP':'28', 'COMPF':'88', 'COMPR':'A0', 'DIV':'24', 'DIVF':'64',
           'DIVR':'9C', 'FIX':'C4', 'FLOAT':'C0', 'HIO':'F4', 'J':'3C',
           'JEQ':'30', 'JGT':'34', 'JLT':'38', 'JSUB':'48', 'LDA':'00',
           'LDB':'68', 'LDCH':'50', 'LDF':'70', 'LDL':'08', 'LDS':'6C',
           'LDT':'74', 'LDX':'04', 'LPS':'D0', 'MUL':'20', 'MULF':'60',
           'MULR':'98', 'NORM':'C8', 'OR':'44', 'RD':'D8', 'RMO':'AC',
           'RSUB':'4C', 'SHIFTL':'A4', 'SHIFTR':'A8', 'SIO':'F0', 'SSK':'EC',
           'STA':'0C', 'STB':'78', 'STCH':'54', 'STF':'80', 'STI':'D4',
           'STL':'14', 'STS':'7C', 'STSW':'E8', 'STT':'84', 'STX':'10',
           'SUB':'1C', 'SUBF':'5C', 'SUBR':'94', 'SVC':'B0', 'TD':'E0',
           'TIO':'F8', 'TIX':'2C', 'TIXR':'B8', 'WD':'DC'}

SYMTAB = {}

LOCCTR = 0

FORM1 = {"FIX":"C4", "FLOAT":"C0", "HIO":"F4", "NORM":"C8", "SIO":"F0", 
         "TIO":"F8"}
FORM2 = {"ADDR":"90", "CLEAR":"B4", "COMPR":"A0", "DIVR":"9C", "MULR":"98",
         "RMO":"AC", "SHIFTL":"A4", "SHIFTR":"A8", "SUBR":"94", "SVC":"B0",
         "TIXR":"B8"}

REGS = {"A":"0", "X":"1", "L":"2", "B":"3", "S":"4", "T":"5", "F":"6",
        "PC":"8", "SW":"9"}

def FindColumn(strline):
    # This function splits each line into a list and then checks to see if
    # the first element is in the opcodes dictionary. If not, we know it is
    # a variable name. If it is in the dictionary, we insert an empty string
    # at the beginning of the list. Therefore, we can distinguish between
    # labels, mnemonics, operands and comments. The first index will always
    # be a label, the second will be a mnemonic, the third will be an operand
    # and the last will be a comment, which we remove from the list.

    # We create an empty string to replace tabs
    newstrline = ""

    # We search for tabs in the string and replace them with spaces in new file
    for char in strline:

        # If we find a tab, we add a space to the new string
        if (char == '\t'):
            newchar = ' '
            newstrline += newchar

        # Otherwise we add the character to the new string
        else:
            newstrline += char

    # Initialize empty array to hold each column
    columns = []

    # We check to see if there is a label or not
    if (newstrline[0] == ' '):
        
        # If there is a space, there is no label so we create an empty column
        columns.append("    ")
            
    # We split the new string based on the spaces
    precols = newstrline.split()

    # We add each of the elements of the split string into the columns list
    for elem in precols:
        columns.append(elem)

    # If the length of the list is greater than 3, we delete all elements
    # in the list after index 2 because they are comments
    if (len(columns) > 3):
        while (len(columns) > 3):
            columns.pop()

    # We want the length to be exactly 3, so we append empty strings
    if (len(columns) < 3):
        while (len(columns) < 3):
            columns.append("")

    return columns

def FindOffset(columns):
    # This function finds the offset of each line in the input file and
    # assigns it to index 0 of each row in the table passed as a parameter

    # The offset of each line is determined by the LOCCTR global variable
    global LOCCTR

    if (columns[1] == "BASE" or columns[0][0] == '.'):
        columns.insert(0, "     ")
        return

    # Insert the hexadecimal offset at index 0
    columns.insert(0, hex(LOCCTR)[2:].zfill(5))

    if (columns[2] == "START"):
        LOCCTR = int(columns[3], 16)

    # Finds how many bytes to add to the offset based on the mnemonic
    elif (columns[2] in FORM2):
        LOCCTR += 2

    elif (columns[2] in FORM1):
        LOCCTR += 1

    elif (columns[2][0] == "+"):
        LOCCTR += 4

    elif (columns[2] == "RESW"):
        LOCCTR += (int(columns[3]) * 3)

    elif (columns[2] == "RESB"):
        LOCCTR += int(columns[3])

    elif (columns[2] == "WORD"):
        LOCCTR += 3

    elif (columns[2] == "BYTE"):
        if (columns[3][0] == 'C'):
            LOCCTR += len(columns[3]) - 3

        elif (columns[3][0] == 'X'):
            counter = 0
            
            for char in columns[3]:
                counter += 1

            counter = counter - 3

            LOCCTR += counter / 2

        else:
            LOCCTR += 1

    else:
        LOCCTR += 3

    return

def FillSymTab(columns):

    # Checks for a label, if none then return
    if columns[1] == "    ":
        return

    elif (columns[1] == '.'):
        return

    # Otherwise we add a new key:value pair to the symbol table
    else:
        SYMTAB[columns[1]] = columns[0]
        return

def FirstPass(filename):

    parseinfo = []

    # Open the file specified in the command line
    with open(filename) as inputFile:

        # Iterate through each line in the input file
        for line in inputFile:
            # Creates a list of each string in the line
            cols = FindColumn(line)

            parseinfo.append(cols)

            # Finds the offset of each line
            FindOffset(cols)

            if (cols[1] == '.'):
                continue

            # Checks for labels and adds to the symbol table
            FillSymTab(cols)

        print("Symbol Table:")
        for elem in SYMTAB:
            print(elem),
            print("  :  "),
            print(SYMTAB.get(elem))
        print('\n')

    return parseinfo
    
def NIbits(operand):

    addint = 0

    if (operand[0] == '#'):
        addint = 1

    elif (operand[0] == '@'):
        addint = 2

    else:
        addint = 3

    return addint

def FindOpcode(opcode, operand):

    # We convert the opcode (string) from hex to an integer
    intval = int(opcode, 16)

    # We check for RSUB and add 3
    if (opcode == "4C"):
        intval += 3

    # Otherwise, we find the value of the n and i bits
    else:
        # We add the value returned to the value of the opcode
        intval += NIbits(operand)

    # We convert the new integer into a hex string
    codeval = hex(intval)[2:]

    return codeval.zfill(2)

def Format4(opcode, operand, curraddr):

    # Initilializing empty string to return
    formatstring = ""

    code = OPTAB.get(opcode[1:])

    # Insert the opcode into the string
    formatstring += FindOpcode(code, operand)

    # Insert the XBPE bits into the string
    formatstring += XBPE(opcode, operand, curraddr)

    # There is an exception for RSUB
    if (opcode == "RSUB"):
        
        # We add 4 0's to the string in the case of +RSUB
        formatstring += "0000"
        
        return formatstring

    # Check if operand is immediate or indirect 
    if (operand[0] == '#' or operand[0] == '@'):

        # We remove the leading character
        newstr = operand[1:]

        # We check if the operand is in the symbol table
        if (newstr in SYMTAB):
            # We insert the correct address retrieved from the symbol table
            formatstring += SYMTAB.get(newstr)

        # Otherwise, we know that it is a constant value > 4096
        else:
            # Get last 5 digits of value and convert to hex and append
            formatstring += hex(int(newstr))[2:].zfill(5)

    # Check if the operand uses index
    elif (operand[len(operand) - 1] == 'X'):
        
        if (operand[:len(operand) - 2] in SYMTAB):
            formatstring += SYMTAB.get(operand[:len(operand) - 2])

        else:
            print("Error: Operand not a label.")

    # We check if the operand is in the symbol table
    elif (operand in SYMTAB):
        
        # Retrieve the address from the symbol table
        formatstring += SYMTAB.get(operand)

    # Otherwise, print error
    else:
        print("Error: Incorrect format 4 instruction")

    return formatstring

def TwoComp(disp):

    # Convert the integer into a binary string
    bin_disp = bin(disp)[3:].zfill(12)

    newbin = ""

    # Iterate through the binary string and flip each of the bits
    for char in bin_disp:
        if (char == '0'):
            newbin = newbin + '1'
        else:
            newbin = newbin + '0'

    hexdisp = hex((int(newbin, 2) + 1))[2:].zfill(3)

    return hexdisp

def Format3(opcode, operand, curraddr, baseaddr):
    
    # Initialize empty string to return
    formatstring = ""

    # Check for START and END directives
    if (opcode == "START"):
        return ""

    elif (opcode == "END"):
        return ""

    # Get the opcode for the instruction from OPTABLE
    codeval = str(OPTAB.get(opcode))

    # We insert the opcode into the string
    formatstring += FindOpcode(codeval, operand)

    formatstring += XBPE(opcode, operand, curraddr)

    # Special case for RSUB
    if (opcode == "RSUB"):
        formatstring += "000"
        return formatstring

    # Find the address of the next instruction
    nextaddr = int(curraddr, 16) + 3

    # We are adding an immediate value
    if (operand[0] == '#' or operand[0] == '@'):

        # Check if the operand is in the symbol table
        if (operand[1:] in SYMTAB):

            labeladdr = SYMTAB.get(operand[1:])

            # We check if displacement is not in range for PC addressing
            if ((int(curraddr, 16) + 3) - int(labeladdr, 16) > 2047 or \
                (int(curraddr, 16) + 3) - int(labeladdr, 16) < -2048):

                # We find the displacement between label address and base
                basevar = (int(labeladdr, 16) - int(baseaddr, 16))

                # We add the displacement to the string
                formatstring += str(basevar).zfill(3)

            # Otherwise, we use PC-relative addressing
            else:
                # We check if we need to do 2's complement
                disp = int(labeladdr, 16) - nextaddr

                # We check if the displacement is negative
                if (disp < 0):
                    # We do 2's complement on the displacement
                    formatstring += TwoComp(disp).zfill(3)

                # Otherwise, we add the displacement to the string
                else:
                    formatstring += hex(disp)[2:].zfill(3)

        # Otherwise we know it is a decimal number
        else:

            # Get last 3 digits of value and convert to hex
            formatstring += hex(int(operand[1:]))[2:].zfill(3)

    # Otherwise, we know that the instruction uses simple addressing
    else:

        # Check if operand has ',X'
        if (operand[len(operand) - 1] == 'X'):
            operand = operand[:len(operand) - 2]

        # We find the address of the label in the operand
        labeladdr = str(SYMTAB.get(operand))

        # We check if displacement is not in range for PC-relative addressing
        if ((int(curraddr, 16) + 3) - int(SYMTAB.get(operand), 16) > 2047 or \
            (int(curraddr, 16) + 3) - int(SYMTAB.get(operand), 16) < -2048):

            basevar = int(labeladdr, 16) - int(baseaddr, 16)

            formatstring += str(basevar).zfill(3)

        else:   
            # We compare the two addresses to see if we use 2's complement
            if (int(labeladdr, 16) > nextaddr):

                # Label address in decimal representation
                intlabel = int(labeladdr, 16)
            
                dispint = (intlabel - nextaddr)

                # We find last 3 digits of displacement of addresses
                disp = hex(dispint)[2:].zfill(3)

                # We append the displacement to the string
                formatstring += disp
        
            # Otherwise, we need to use 2's complement
            else:
                # Label address in decimal representation
                intlabel = int(labeladdr, 16)

                disp = intlabel - nextaddr
                formatstring += TwoComp(disp)

    return formatstring

def Format2(opcode, operand):

    # Initialize empty string to return
    formatstring = ""

    # Get the opcode for the format 2 instruction
    formatstring += FORM2.get(opcode)
    
    # Bool to determine if there are 2 values in the operand
    tworegs = False

    # Check if there are 2 values in the operand
    for char in operand:

        # If we find ',' then we know there are 2 values in the operand
        if (char == ','):
            tworegs = True

    # This will be false for some format 2 instructions
    if (tworegs):

        # Split the registers into two different elements
        reglist = operand.split(',')

        # We check if both values in the operand are registers
        if (reglist[0] in REGS and reglist[1] in REGS):
        
            # Add both register values to the string
            formatstring += REGS.get(reglist[0])
            formatstring += REGS.get(reglist[1])
            return formatstring
    
        # We check if the first register is SHIFTL or SHIFTR
        elif (opcode == "SHIFTL" or opcode == "SHIFTR"):

            # We get the register value
            formatstring += REGS.get(reglist[0])        

            # We subtract 1 from the value
            reg2 = int(reglist[1]) - 1

            formatstring += hex(reg2)[2:]

        else:
            # Print an error message, register does not exist
            print("1")

    # We check if the operand is a register
    elif (operand in REGS):
        
        # We add the value of the register to the string
        formatstring += REGS.get(operand)

        # We add a '0' because there is not second value
        formatstring += '0'

    # Otherwise, we know the operand is a decimal value
    else:
        # We add the hex value of the operand to the string
        formatstring += hex(int(operand))[2:]

        # We add a '0' because there is not a second value
        formatstring += '0'

    return formatstring
    

def XBPE(opcode, operand, curraddr):

    midbits = 0

    # If there is no operand, we return 0
    if (operand == ''):
        return '0'

    # Check if operand is indexed
    if (operand[len(operand) - 1] == 'X'):
        midbits += 8

        # Remove ',X' from the operand for rest of function
        operand = operand[:len(operand) - 2]

    # This will be true if the instruction is format 4
    if (opcode[0] == '+'):
        midbits += 1

        final = hex(midbits)[2:]
        return final

    if (operand[0] == '#' or operand[0] == '@'):
        operand = operand[1:]

    # Otherwise, we know the instruction is format 3
    if (operand in SYMTAB):

        # We check if displacement is not in range for PC-relative addressing
        if ((int(curraddr, 16) + 3) - int(SYMTAB.get(operand), 16) > 2047 or \
            (int(curraddr, 16) + 3) - int(SYMTAB.get(operand), 16) < -2048):

            # We add 4 for 'b' bit
            midbits += 4
        
        # Otherwise, we know the instruction uses PC-relative addressing
        else:
            # We add 2 for the 'p' bit
            midbits += 2      

    return hex(midbits)[2:]

def FindForm(opcode):

    # Determine if the instruction format is format 4
    if (opcode[0] == '+'):
        return 4

    # Otherwise, we know the instruction is format 3
    else:
        return 3

def SecondPass(infolist, target):

    basevar = '0'

    for elem in infolist:
        instrform = ""

        # Bool to check for format 1/2
        handled = False

        # Get the instruction from the table
        code = elem[2]

        # Check for the RESB directive
        if (code == "RESB"):

            # Find the number of 0's to add to the string
            addzero = int(elem[3]) * 2

            # Add the correct number of 0's to the string
            for c in range(0, addzero):
                instrform += "0"

        # Check for the RESW directive
        elif (code == "RESW"):

            # Multiply the operand by 6 to get the number of bytes
            addzero = int(elem[3]) * 6

            # We add the correct number of 0's to the string
            for c in range(0, addzero):
                instrform += "0"

        # We check if the row is a comment
        elif (elem[1][0] == '.'):
            continue

        elif (code == "START"):
            continue

        elif (code == "END"):
            continue

        # We check for the BYTE directive
        elif (code == "BYTE"):
            
            # We check if the operand is given as a hex constant
            if (elem[3][0] == 'X'):

                # Add the operand to the string
                instrform += str(elem[3][2:len(elem[3]) - 1].zfill(2))

            # We check if the operand is given as characters
            elif (elem[3][0] == 'C'):

                # Find the operand
                newstr = elem[3][2:len(elem[3]) - 1]
                
                # Iterate through each character and convert to integer
                for char in newstr:
                    newchar = ord(char)
                    instrform += hex(newchar)[2:]

            # Otherwise we know it is a decimal value
            else:

                # Convert the decimal value into a string
                newstr = str(elem[3])

                # Add the hex value of the decimal string to the final string
                instrform += hex(newstr)

        # We check for the WORD directive
        elif (code == "WORD"):

            # Add the hex value of the decimal string to the final string
            instrform += hex(int(elem[3]))[2:].zfill(6)
        
        # We check if the BASE register is set
        elif (code == "BASE"):
            basevar = SYMTAB.get(elem[3])

        # Handle format 1 instructions
        elif (code in FORM1):
            instrform += FORM1.get(code)
            handled = True

        # Handle format 2 instructions
        elif (code in FORM2):
            instrform += Format2(code, elem[3])
            handled = True

        # If the instruction is in neither, we check if it is in OPTABLE
        elif (code in OPTAB or code[1:] in OPTAB):
            # Find format of the instruction (3/4)
            format = FindForm(code)

            # Handle format 4 instructions
            if (format == 4):

                instrform += Format4(code, elem[3], elem[0])

            # Handle format 3 instructions
            elif (format == 3):
                instrform += Format3(code, elem[3], elem[0], basevar)

        # Otherwise, if none above, return an error
        else:
            print("Error: Instruction not valid - "),
            print(code)

        # Append the instruction string to the list in the table
        elem.append(instrform)

        # Convert the instruction format to ASCII characters
        writebytes = ''.join(chr(int(instrform[i:i+2], 16)) \
                             for i in range(0, len(instrform), 2))

        # Write the instruction to the .exe file
        target.write(writebytes)

        # Loop to print table to screen
        for col in elem:
            if (col == "RESB" or col == "RESW"):
                print(col),
                print('\t'),
                print(elem[3]),
                break
            else:
                print(col),           
                print("\t"),

        print('')

    return

def NewFile(filename):

    # Create a new .exe file using filename from command line arguments
    newfile = filename[:len(filename) - 4] + ".exe"

    return newfile

def main():

    # Create new target file to write to
    target = open(NewFile(sys.argv[1]), 'w')

    # Create a table of row elements and symbol table
    parseline = FirstPass(sys.argv[1])

    # Assemble the instructions and write to .exe file
    SecondPass(parseline, target)

    return

if __name__ == "__main__":
    main()
