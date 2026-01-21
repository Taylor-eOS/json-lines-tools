input_basename = 'input'

def clean_preamble(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
    cleaned_lines = []
    i = 0
    while i < len(lines):
        if (i + 3 < len(lines) and
            lines[i].startswith('||') and
            lines[i+1].startswith('[]') and
            lines[i+2].startswith('[]') and
            lines[i+3].strip() == '|'):
            i += 4
        else:
            cleaned_lines.append(lines[i])
            i += 1
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(cleaned_lines)

clean_preamble(input_basename + '.txt', input_basename + '_cleaned.txt')
print('Done')
