from collections import defaultdict

approved_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZæøåÆØÅ0123456789äöüÄÖÜß .,!?:;"\'()-_/@#%&*+=|\\ {}<>’‘“”—–[]áéíóúñàèìòùê$»«'
approved_set = set(approved_chars)
context_before = 40
context_after = 20

if __name__ == '__main__':
    filename = input('Input file: ').strip() or 'input.json'
    try:
        char_locations = defaultdict(list)
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for col, c in enumerate(line):
                    if c not in approved_set and c.isprintable():
                        char_locations[c].append((line_num, col, line))
    except FileNotFoundError:
        print('File not found')
        exit(1)
    except UnicodeDecodeError:
        print('File is not valid UTF-8')
        exit(1)
    except Exception as e:
        print('Error reading file:', e)
        exit(1)
    if not char_locations:
        print('No unwanted printable characters found in the file.')
        exit(0)
    sorted_chars = sorted(char_locations.keys(), key=lambda c: (ord(c), c))
    total_occurrences = sum(len(loc) for loc in char_locations.values())
    print(f'Found {len(sorted_chars)} characters') #({total_occurrences} occurrences).')
    print('Enter to see the next character, q to quit.')
    for char_idx, bad_char in enumerate(sorted_chars, 1):
        line_num, col, line_text = char_locations[bad_char][0]
        expanded = line_text.rstrip('\n\r').expandtabs(8)
        pos = len(line_text[:col].expandtabs(8))
        start = max(0, pos - context_before)
        snippet = expanded[start:pos + context_after + 1]
        display_snippet = snippet
        if start > 0:
            display_snippet = '...' + display_snippet
        if pos + context_after < len(expanded):
            display_snippet += '...'
        appearances = len(char_locations[bad_char])
        print(f'{char_idx}/{len(sorted_chars)}: "{bad_char}" (U+{ord(bad_char):04X}) appears {appearances} time{"s" if appearances > 1 else ""}')
        print(f'Example at line {line_num}:') #, position {col + 1}')
        print(display_snippet)
        action = input('->').strip().lower()
        if action == 'q':
            print('Stopped early.')
            break
    else:
        print('Finished showing one examples.')

