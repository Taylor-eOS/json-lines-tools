LIGATURE_MAP = {
    '\ufb00': 'ff',   # ﬀ
    '\ufb01': 'fi',   # ﬁ
    '\ufb02': 'fl',   # ﬂ
    '\ufb03': 'ffi',  # ﬃ
    '\ufb04': 'ffl',  # ﬄ
    '\ufb05': 'ft',   # ﬅ 
    '\ufb06': 'st'    # ﬆ
}

def replace_ligatures(text):
    result = text
    for lig, plain in LIGATURE_MAP.items():
        result = result.replace(lig, plain)
    return result

if __name__ == '__main__':
    filename = input('Input file: ').strip()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print('File not found')
        exit(1)
    except UnicodeDecodeError:
        print('File is not valid UTF-8')
        exit(1)
    except Exception as e:
        print('Error reading file:', e)
        exit(1)
    cleaned = replace_ligatures(text)
    new_filename = filename.rsplit('.', 1)
    if len(new_filename) == 2:
        new_filename = new_filename[0] + '_clean.' + new_filename[1]
    else:
        new_filename = filename + '_clean'
    try:
        with open(new_filename, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print('Saved as:', new_filename)
    except Exception as e:
        print('Error writing file:', e)

