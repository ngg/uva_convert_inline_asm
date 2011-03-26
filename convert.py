import sys, os, argparse

def main():
	cstart = '''int main(void)
{
    __asm__ __volatile__ (
\"jmp aftermainorig\\n"
'''

	cend = '''".text\\n"
"aftermainorig:\\n"
    );
    __asm__ __volatile__ ("call %s" : : : "cc", "memory", "eax", "ecx", "esi", "edi");
    return 0;
}

'''
	skip = ('.file', '.size', '.ident', '.globl', '.cfi', '.weakref', '.weak ', '.section .text.')
	repl = [('"', '\\"'), ('\t', ' '), ('  ', ' '), ('.L', '.LL')]
	repl_c = [('__isoc99_', '')]
	repl_cpp = []

	parser = argparse.ArgumentParser(description='Compile C/C++ to inline ASM.', epilog='Do not include <iostream>!')
	parser.add_argument('-i', '--input', default=None)
	parser.add_argument('-o', '--output', default=None)
	parser.add_argument('-p', '--cpp', action='store_true')
	parser.add_argument('-n', '--no-compress', dest='compress', action='store_false')
	args = parser.parse_args()

	infile = sys.stdin
	outfile = sys.stdout

	if args.input != None:
		infile = open(args.input, 'r')
	if args.output != None:
		outfile = open(args.output, 'w')

	with open('toasm_tmp.c', 'w') as tmpc:
		tmpc.write('#define main mainorig\n')
		tmpc.write(infile.read())

	if args.cpp:
		compstr = 'g++ -m32 -O3 -ffast-math -fomit-frame-pointer -S toasm_tmp.c'
	else:
		compstr = 'gcc -m32 -O3 -ffast-math -fomit-frame-pointer -S toasm_tmp.c'

	assert os.system(compstr) == 0, ''.join(['Compile error (', compstr, ')'])	

	lines = []
	with open('toasm_tmp.s', 'r') as tmps:
		for line in tmps:
			line = line.strip()
			for (old, new) in repl:
				line = line.replace(old, new)
			if args.cpp:
				for (old, new) in repl_cpp:
					line = line.replace(old, new)
			else:
				for (old, new) in repl_c:
					line = line.replace(old, new)
			if line.find('mainorig') != -1 and line.endswith(':'):
				mainorigname = line[0:-1]
			if not line.startswith(skip):			
				lines.append(''.join(['"', line, '\\n"']))

	if args.compress:
		cnt = {}
		for line in lines:
			if line in cnt:
				cnt[line] += 1
			else:
				cnt[line] = 1
		short = {}
		sn = firstname()
		for (line, c) in sorted(cnt.iteritems(), key=lambda (k,v): (v,k), reverse=True):		
			if 10+len(sn)*(c+1) < len(line)*(c-1):
				outfile.write('#define ')
				outfile.write(''.join(sn))
				outfile.write(' ')
				outfile.write(line)
				outfile.write('\n')
				short[line] = ''.join(sn)
				sn = nextname(sn)
			else:
				short[line] = line

		outfile.write(cstart);
		for line in lines:
			outfile.write(short[line])
			outfile.write('\n')
		outfile.write(cend % (mainorigname));
	else:
		outfile.write(cstart);
		for line in lines:
			outfile.write(line)
			outfile.write('\n')
		outfile.write(cend % (mainorigname));

	os.unlink('toasm_tmp.c')
	os.unlink('toasm_tmp.s')
	infile.close()
	outfile.close()

def firstname():
	def charrange(start, end):
		return map(chr, range(ord(start), ord(end)+1))

	global name_chars
	name_chars = []
	name_chars.extend(charrange('A', 'Z'))
	name_chars.extend(charrange('a', 'z'))
	name_chars.extend(charrange('0', '9'))
	name_chars.append('_')

	global name_chars_first
	name_chars_first = []
	name_chars_first.extend(charrange('A', 'Z'))

	return [name_chars_first[0]]

def nextname(name):
	global name_chars
	global name_chars_first

	def constendlist(start, next, n, end):
		start.append(next)
		for i in xrange(n):
			start.append(end)
		return start

	for i in xrange(len(name)-1, 0, -1):
		if name[i] != name_chars[-1]:
			return constendlist(name[0:i], name_chars[name_chars.index(name[i])+1], len(name)-i-1, name_chars[0])
	if name[0] != name_chars_first[-1]:
		return constendlist([], name_chars_first[name_chars_first.index(name[0])+1], len(name)-1, name_chars[0])
	return constendlist([], name_chars_first[0], len(name), name_chars[0])

if __name__ == "__main__":
	main()
