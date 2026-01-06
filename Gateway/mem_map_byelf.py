from elftools.elf.elffile import ELFFile
import re
import os
import datetime

# Patterns for library-related or non-user-defined variables
EXCLUDE_PATTERNS = [
    r'^RCC_.*', r'^GPIO_.*', r'^hspi$', r'^tickstart$', r'^status$', r'^pllvco$',
    r'^pllp$', r'^pllsource$', r'^pllm$', r'^pid$', r'^length$', r'^addr$',
    r'^wait$', r'^prevTickFreq$', r'^prioritygroup$', r'^reg_value$',
    r'^stream_number$', r'^flagBitshiftOffset$', r'^timeout$', r'^regs$',
    r'^mask_cpltlevel$', r'^odr$', r'^bitstatus$', r'^position$', r'^ioposition$',
    r'^iocurrent$', r'^sysclockfreq$', r'^pll_config$', r'^pwrclkchanged$',
    r'^itsource$', r'^itflag$', r'^errorcode$', r'^abortcplt$', r'^txallowed$',
    r'^initial_TxXferCount$', r'^tmp_.*', r'^hspi*', r'^special*', r'^hi2c*',r'^dp*' ,r'^__sbrk*',
]

# Type mapping from C types to stdint types
TYPE_MAPPING = {
    'char': 'int8_t',
    'signed char': 'int8_t',
    'unsigned char': 'uint8_t',
    'short': 'int16_t',
    'short int': 'int16_t',
    'signed short': 'int16_t',
    'signed short int': 'int16_t',
    'short unsigned int': 'uint16_t',
    'unsigned short': 'uint16_t',
    'unsigned short int': 'uint16_t',
    'int': 'int32_t',
    'signed int': 'int32_t',
    'unsigned int': 'uint32_t',
    'long': 'int32_t',
    'long int': 'int32_t',
    'signed long': 'int32_t',
    'signed long int': 'int32_t',
    'long unsigned int': 'uint32_t',
    'unsigned long': 'uint32_t',
    'unsigned long int': 'uint32_t',
    'long long': 'int64_t',
    'long long int': 'int64_t',
    'signed long long': 'int64_t',
    'signed long long int': 'int64_t',
    'unsigned long long': 'uint64_t',
    'unsigned long long int': 'uint64_t',
}

# Enable debug mode - set to True to see detailed output
DEBUG = False

def debug_print(msg):
    """Print debug messages if DEBUG is enabled."""
    if DEBUG:
        print(f"[DEBUG] {msg}")

def normalize_type(type_str):
    """Convert C type names to stdint type names."""
    # Handle pointer types
    if type_str.endswith('*'):
        base_type = type_str[:-1].strip()
        if base_type in TYPE_MAPPING:
            return TYPE_MAPPING[base_type] + '*'
        return type_str
    
    # Handle regular types
    if type_str in TYPE_MAPPING:
        return TYPE_MAPPING[type_str]
    
    return type_str

def is_user_defined_variable(name):
    """Check if the variable name is likely user-defined."""
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, name):
            return False
    return True

def get_memory_address(location):
    """Parse DWARF location expression to extract memory address in little-endian format."""
    try:
        if location[0] == 3:  # DW_OP_addr
            addr_bytes = location[1:5]  # Assuming 4-byte address
            address = sum(b << (i * 8) for i, b in enumerate(addr_bytes))
            return f"0x{address:08x}"
        return str(location)
    except:
        return str(location)

def find_die_by_offset(dwarfinfo, target_offset, cu_offset=None):
    """Find a DIE by its offset.
    
    Args:
        dwarfinfo: DWARF info object
        target_offset: Target DIE offset (can be absolute or CU-relative)
        cu_offset: If provided, target_offset is treated as CU-relative
    """
    try:
        # If CU offset provided, convert to absolute offset
        if cu_offset is not None:
            target_offset = cu_offset + target_offset
        
        for cu in dwarfinfo.iter_CUs():
            for die in cu.iter_DIEs():
                if die.offset == target_offset:
                    return die
        return None
    except:
        return None

def get_type_info(dwarfinfo, die, var_name="", cu_offset=None):
    """Recursively get complete type information for a DIE.
    
    Args:
        dwarfinfo: DWARF info object
        die: Current DIE to analyze
        var_name: Variable name for debug messages
        cu_offset: Compilation unit offset for resolving CU-relative references
    """
    if not die:
        debug_print(f"No DIE found for '{var_name}'")
        return 1, "Unknown"
    
    debug_print(f"Analyzing type for '{var_name}': tag={die.tag}, offset={die.offset}")
    
    # Print all attributes for debugging
    if DEBUG and var_name:
        for attr_name, attr_value in die.attributes.items():
            debug_print(f"  {attr_name}: {attr_value}")
    
    # Handle different type tags
    if die.tag == "DW_TAG_array_type":
        debug_print(f"  Found array type for '{var_name}'")
        
        # Get array dimensions
        element_count = None
        for child in die.iter_children():
            if child.tag == "DW_TAG_subrange_type":
                if "DW_AT_count" in child.attributes:
                    element_count = child.attributes["DW_AT_count"].value
                    debug_print(f"  Array count: {element_count}")
                elif "DW_AT_upper_bound" in child.attributes:
                    element_count = child.attributes["DW_AT_upper_bound"].value + 1
                    debug_print(f"  Array upper bound: {element_count - 1}, count: {element_count}")
                break
        
        # Get element type
        if "DW_AT_type" in die.attributes:
            element_type_offset = die.attributes["DW_AT_type"].raw_value
            element_die = find_die_by_offset(dwarfinfo, element_type_offset, cu_offset)
            _, base_type = get_type_info(dwarfinfo, element_die, f"{var_name}[element]", cu_offset)
            return element_count if element_count else 1, base_type
        
        return element_count if element_count else 1, "Unknown"
    
    elif die.tag == "DW_TAG_subrange_type":
        # Handle subrange_type directly (collapsed array representation)
        debug_print(f"  Found subrange type (collapsed array) for '{var_name}'")
        
        element_count = None
        if "DW_AT_count" in die.attributes:
            element_count = die.attributes["DW_AT_count"].value
            debug_print(f"  Array count: {element_count}")
        elif "DW_AT_upper_bound" in die.attributes:
            element_count = die.attributes["DW_AT_upper_bound"].value + 1
            debug_print(f"  Array upper bound: {element_count - 1}, count: {element_count}")
        
        # Get base type from the subrange's type
        base_type = "Unknown"
        if "DW_AT_type" in die.attributes:
            base_type_offset = die.attributes["DW_AT_type"].raw_value
            base_die = find_die_by_offset(dwarfinfo, base_type_offset, cu_offset)
            _, base_type = get_type_info(dwarfinfo, base_die, f"{var_name}[base]", cu_offset)
        
        return element_count if element_count else 1, base_type
    
    elif die.tag in ["DW_TAG_typedef", "DW_TAG_const_type", "DW_TAG_volatile_type"]:
        debug_print(f"  Following {die.tag} for '{var_name}'")
        
        if "DW_AT_type" in die.attributes:
            next_type_offset = die.attributes["DW_AT_type"].raw_value
            next_die = find_die_by_offset(dwarfinfo, next_type_offset, cu_offset)
            return get_type_info(dwarfinfo, next_die, var_name, cu_offset)
        
        return 1, "Unknown"
    
    elif die.tag == "DW_TAG_base_type":
        if "DW_AT_name" in die.attributes:
            type_name = die.attributes["DW_AT_name"].value.decode()
            debug_print(f"  Base type for '{var_name}': {type_name}")
            # Normalize the type name to stdint format
            normalized_type = normalize_type(type_name)
            return 1, normalized_type
        return 1, "Unknown"
    
    elif die.tag == "DW_TAG_pointer_type":
        debug_print(f"  Pointer type for '{var_name}'")
        if "DW_AT_type" in die.attributes:
            next_type_offset = die.attributes["DW_AT_type"].raw_value
            next_die = find_die_by_offset(dwarfinfo, next_type_offset, cu_offset)
            _, base_type = get_type_info(dwarfinfo, next_die, var_name, cu_offset)
            return 1, f"{base_type}*"
        return 1, "void*"
    
    elif die.tag == "DW_TAG_structure_type":
        if "DW_AT_name" in die.attributes:
            struct_name = die.attributes["DW_AT_name"].value.decode()
            debug_print(f"  Structure type for '{var_name}': {struct_name}")
            return 1, struct_name
        return 1, "struct"
    
    else:
        debug_print(f"  Unhandled tag for '{var_name}': {die.tag}")
        return 1, "Unknown"

# Check if ELF file exists
elf_file_path = "./STM32F4VE_tst.elf"
if not os.path.exists(elf_file_path):
    print(f"ELF file '{elf_file_path}' not found.")
    exit(1)

elf_basename = os.path.splitext(os.path.basename(elf_file_path))[0]
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
output_dir = "../data/csv"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, f"{elf_basename}_{timestamp}.csv")

user_defined_vars = []
missing_type_vars = []

try:
    with open(output_csv, "w") as csv_file:
        csv_file.write("Variable,Address,No of Elements,Type\n")
        
        elf = ELFFile(open(elf_file_path, "rb"))
        
        if not elf.has_dwarf_info():
            print("No DWARF info found in the ELF file.")
            exit(1)
        
        dwarfinfo = elf.get_dwarf_info()
        variable_found = False
        
        for CU in dwarfinfo.iter_CUs():
            cu_offset = CU.cu_offset  # Get the compilation unit offset
            
            for DIE in CU.iter_DIEs():
                if DIE.tag == "DW_TAG_variable":
                    name = DIE.attributes.get("DW_AT_name")
                    loc = DIE.attributes.get("DW_AT_location")
                    vartype = DIE.attributes.get("DW_AT_type")
                    
                    if name and loc:
                        variable_name = name.value.decode()
                        address = get_memory_address(loc.value)
                        
                        # Skip variables without proper addresses
                        if address.startswith("[145,"):
                            continue
                        
                        if is_user_defined_variable(variable_name):
                            variable_found = True
                            
                            debug_print(f"\n=== Processing variable: {variable_name} at {address} ===")
                            debug_print(f"CU offset: {cu_offset}")
                            
                            # Get variable type information
                            if vartype:
                                type_offset = vartype.raw_value
                                debug_print(f"Type offset: {type_offset} (CU-relative), absolute: {cu_offset + type_offset}")
                                type_die = find_die_by_offset(dwarfinfo, type_offset, cu_offset)
                                if type_die:
                                    elements, var_type = get_type_info(dwarfinfo, type_die, variable_name, cu_offset)
                                else:
                                    debug_print(f"WARNING: Could not find DIE at offset {type_offset} (absolute: {cu_offset + type_offset}) for {variable_name}")
                                    elements = 1
                                    var_type = "Unknown"
                                    missing_type_vars.append(f"{variable_name} (offset {type_offset} not found)")
                            else:
                                elements = 1
                                var_type = "Unknown"
                                debug_print(f"WARNING: No DW_AT_type attribute for {variable_name}")
                                missing_type_vars.append(f"{variable_name} (no DW_AT_type)")
                            
                            csv_line = f"{variable_name},{address},{elements},{var_type}"
                            user_defined_vars.append(csv_line)
                            csv_file.write(f"{csv_line}\n")
        
        if not variable_found:
            print("No user-defined variables found.")
    
    if DEBUG:
        print("\n" + "="*60)
        print("FINAL RESULTS:")
        print("="*60)
    
    if os.path.exists(output_csv) and os.path.getsize(output_csv) > 0:
        print("User defines:")
        for var in user_defined_vars:
            print(var)
        print(f"\nCSV saved to: {output_csv}")
        
        if missing_type_vars:
            print(f"\nWARNING: {len(missing_type_vars)} variables with missing type information:")
            for var in missing_type_vars:
                print(f"  - {var}")
    else:
        print(f"{output_csv} is empty or was not created.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
