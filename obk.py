# TODO:
# * vfs:parent
# * stop using res(%d)
# * move more logic into alvo
# * use alvo for postprocessing, (actual file operations)
#   * actually integrate HiStore
#   * move files into place (poss. across filesystems)
import os, time, stat, hashlib, sys
from typing import List

from help import *


def _sha256(bytes):
	hasher = hashlib.sha256()
	hasher.update(bytes)
	return hasher

# s256 = _sha256.sha256()
# s256.update(b'abc')
# hd = s256.hexdigest()
#
# print (hd)

# from alvo import *

# try:
# 	from java.lang import Object as object
# except:
# 	pass


PERM_MASK = 0o777


class G:
	def __init__(self, filename: str):
		if isinstance(filename, str):
			self.xx = open(filename, 'w')
	
	def write(self, x):
		self.xx.write(x)
	
	def Assert(self, subj, pred):
		print(subj, pred, file=self.xx)


class G0:
	def __init__(self, a=None): pass
	
	def write(self, x): pass
	
	def Assert(self, subj, pred): pass


def get_username_and_groupname(a_uid, a_gid):
	import pwd, grp
	uis = pwd.getpwuid(a_uid).pw_name
	gis = grp.getgrgid(a_gid).gr_name
	return uis, gis


# --------------------------------------------------------------
#                              .
# --------------------------------------------------------------

class Printable:
	def printable(self) -> str:
		pass
	
	
class LongAttribute(Printable):
	def __init__(self, n, v):
		self.n = n
		self.v = v
		
	def printable(self) -> str:
		return '%s %ld' % (self.n, self.v)
	
	
class StringAttribute(Printable):
	def __init__(self, n, v):
		self.n = n
		self.v = v
	
	def printable(self) -> str:
		return '%s "%s"' % (self.n, self.v)


class OctalAttribute(Printable):
	def __init__(self, n, v):
		self.n = n
		self.v = v
	
	def printable(self) -> str:
		return '%s 8#%lo' % (self.n, self.v)


class BooleanAttribute(Printable):
	def __init__(self, n, v: bool):
		self.n = n
		self.v = v
	
	def printable(self) -> str:
		return '%s %s' % (self.n, self.v)


class AttributeStore:
	store: List[Printable]
	filename: str
	
	def __init__(self):
		self.store = []
	
	def add_long(self, mode, val):
		""" based on show_diff_lines_long in eachfile.c """
		#
		D = {'l': ' vfs:nlinks', 'u': ' vfs:uid', 'g': ' vfs:gid', 'z': ' vfs:filesize', 'i': ' vfs:inode'}
		x = D[mode]
		#
		self.store.append(LongAttribute(x, val))

	def add_octal(self, mode, val, extra):
		x = ''
		#
		s, p = extra
		#
		assert mode == 'p'  # for mode
		#
		if stat.S_ISLNK(s.st_mode):  # for a symlink ...
			self.store.append(BooleanAttribute('vfs:symlink', True))
			# TODO: catch errors here!!!
			try:
				read1 = os.readlink(p)
				self.store.append(StringAttribute('vfs:symtarget', read1))
			except OSError as e:
				x += ' /rdf1\n\tobk:error-during-readlink "%d"' % e.errno # TODO test this
			assert val == 0o777
		else:
			if stat.S_ISDIR(s.st_mode):  # for a dir ...
				self.store.append(BooleanAttribute('vfs:directory', True))
			self.store.append(OctalAttribute('vfs:mode', val))
		#
		######out.write(' %s /rdf1\n' % x)

	def add_time(self, mode, val):
		""" based on show_diff_time from eachfile.c """
		#
		D = {'a': ' vfs:access-time', 'm': ' vfs:modify-time', 'c': ' vfs:create-time'}
		x = D[mode]
		#
		buf = time.strftime("%Y_%m%b%d-%H:%M:%S", time.localtime(val))
		assert not not buf  # TODO: why do we need assert?
		# if not buf: DIE("strftime") # ??
		self.store.append(StringAttribute(x, buf))

	def add_checksum(self, a_sum):
		self.store.append(StringAttribute('obk:sha256', a_sum))
	
	def show_filename(self, out, name):
		pass
	
	def set_filename(self, name, a_con):
		# _res = 'res%d' % a_con.resource_number
		# a_con.gg.Assert('fn', name)
		# xx = newFile(a_con)
		# out.write('%s obk:res "%s" /rdf1\n  obk:storage "%s" /rdf1\n\t' % (_res, name, xx))
		self.filename = name


class Output3:
	def start(self):
		pass
	
	def show_attributes(self, a_con, out, a_attributes):
		fn = a_attributes.filename

		_res = 'res%d' % a_con.resource_number
		a_con.gg.Assert('fn', fn)
		xx = newFile(a_con)
		out.write('%s obk:res "%s" /rdf1\n  obk:storage "%s" /rdf1' % (_res, fn, xx))

		s = a_attributes.store
		if len(s) == 1:
			h = s[0]
			t = None
		elif len(s) == 0:
			# TODO print notice of no attributes stores
			return
		else:
			h = s[:len(s)-1]
			t = s[-1]
			
		if t is not None:
			[out.write("\n\t%s /rdf1" % x.printable()) for x in h]
			out.write("\n\t%s /rdf0" % t.printable())
		else:
			#assert len(h) == 1
			out.write("\n\t%s /rdf0" % h[0].printable())


class Output4(Output3):
	def _pd(self):
		pass


class ResourceDef(object):
	def __init__(self, a_path):
		self.path = a_path
		self.sum = '<INVALID>'
		self.stat = ('<INVALID>',)
		
	__slots__ = ('path', 'stat', 'sum')


def mk_resource_def(a_filename, a_controller):
	"""@sig public ResourceDef mk_resource_def(String s, Controller c)"""
	R = ResourceDef(a_filename)
	#
	if os.path.islink(a_filename):
		R.stat = os.lstat(a_filename)  # TODO:
	else:
		R.stat = os.stat(a_filename)
	if os.path.isdir(a_filename):  # stat.S_ISDIR(self.stat.st_mode):
		R.sum = '<DIR>'
	elif os.path.islink(a_filename):  # only for symlinks
		R.sum = '<isLINK>'
	else:
		# dont calculate checksums twice for hardlinks
		if R.stat.st_nlink > 1 and R.stat.st_ino in a_controller.nodes:
			R.sum = a_controller.nodes[R.stat.st_ino]
		else:
			try:
				xf = dfile(open(a_filename, 'rb'), None)  # TODO: None was self
				R.sum = _sha256(xf.read()).hexdigest()
			except Exception as e:
				print('-----------------------------')
				print('during %s' % a_filename)
				print('-----------------------------')
				print(e)
				print('-----------------------------')
			else:
				a_controller.nodes[R.stat.st_ino] = R.sum
				xf.close()
	# ~ R.name = a_filename
	# ~ print 167, R.path, R.sum
	return R


def newFile(a_con):
	""" allocate a node in the system and return an identifier for use with obk:storage """
	fn = name_of_inode(Fill(repr(a_con.last_inode)), a_con, cm_content)
	a_con.last_inode += 1
	a_con.gg.Assert('nf', fn)
	return fn


def show_resource_def(a_resource_def, a_output, a_controller):
	"""@sig public static void show_resource_def(ResourceDef rdef, Output3 O, Controller c)"""
	s = a_resource_def.stat
	O = a_controller.A = AttributeStore()
	Out = a_controller.O  # !!
	#
	O.set_filename(a_resource_def.path, a_controller)
	#
	O.add_octal('p', s.st_mode & PERM_MASK, (s, a_resource_def.path))
	O.add_long('i', s.st_ino)
	O.add_long('l', s.st_nlink)
	O.add_long('u', s.st_uid)
	O.add_long('g', s.st_gid)
	if a_resource_def.sum[0] != '<':  # size of dirs and symlinks dont matter
		O.add_long('z', s.st_size)
	O.add_time('a', s.st_atime)
	O.add_time('m', s.st_mtime)
	O.add_time('c', s.st_ctime)
	if a_resource_def.sum[0] != '<':  # a_sum of dirs and symlinks dont exist
		O.add_checksum(a_resource_def.sum)  # , 0)
	a_output.write('\n\n')
	#####a_output.write("\tobk:dummy 'dummy' /rdf0\n")


def postprocess_resource_def(a_resource_def, a_controller):
	"""@sig public static void postprocess_resource_def(ResourceDef a1, Controller a2)"""
	if a_resource_def.sum == '<DIR>':  # and recursive and(or??) name in vals
		# go(os.path.join(a_resource_def.path), a_controller.O, a_controller.gg)
		a_controller.put(Recurse(a_resource_def.path))
		a_controller.gg.Assert('fo', '1')
	else:
		a_controller.gg.Assert('fo', '0')


def main():
	O = Output3()
	O.start()
	xx = sys.argv[1:] or ['.']
	# G      = G0 # !!
	gg = G('ii')
	# key  = [ os.path.join(sd, x ) for x in os.listdir(sd) for sd in xx ] # TODO: create filenamesource
	con = Controller(gg, O)
	rr = [go(sd, con) for sd in xx]
	pass


class Ror: pass


class Recurse(Ror):
	def __init__(self, path):
		self.path = path


class Resource(Ror):
	pass


class Controller(object):
	def __init__(self, gg, O):
		self.resource_number = 1
		self.nodes = {}
		self.gg = gg
		self.O = O
		self.A = AttributeStore()
		self.last_inode = 0
		self._root = time.strftime('%d%H%M%S', time.localtime(time.time()))
		self.__i = []
	
	def get(self, i):
		"""@sig public RoR get(int i)"""  # throws...
		return self.__i[i]
	
	def put(self, v):
		"""@sig public void put(Ror v)"""
		self.__i.append(v)
		
	def putAll(self, vs):
		"""@sig public void put(List<Ror> v)"""
		for v in vs:
			self.__i.append(v)
			
	def save(self, n):
		self.__i = self.__i[n:]  # save memory
		
	__slots__ = ('resource_number', 'nodes', 'gg', 'O', 'A', 'last_inode', '_root', '__i')


class RecursionFlowControl(Exception):
	__slots__ = ('K', 'N')


def go(sd, con):
	try:
		i = 0
		t = True
		key = [os.path.join(sd, x) for x in os.listdir(sd)]  # TODO: create filenamesource
		con.putAll(key)
		while t:
			try:
				t = go1(sd, con, i)
			except IndexError:
				break  # see below
			except RecursionFlowControl as rfc:
				raise rfc
			except Exception as e:
				print(100, 'error during operation >>', (sd, con, i), '<<', e)
				t = False  # TODO: do we really want to stop?
			i += 1
			# if i > len(key):
			# 	t = False
	except RecursionFlowControl as rfc:
		con.save(rfc.N + 1)  # save memory
		go(rfc.K, con)
	except IndexError:
		pass  # presumably from con.get(xx)


def go1(sd, con, n):
	y = con.get(n)
	if isinstance(y, Recurse):
		rfc = RecursionFlowControl()
		rfc.K = y.path
		rfc.N = n
		raise rfc

	# TODO doesn't use Resource
	resource_def = mk_resource_def(y, con)
	
	output_device = sys.stdout
	
	show_resource_def(resource_def, output_device, con)
	postprocess_resource_def(resource_def, con)
	con.resource_number += 1
	con.O.show_attributes(con, output_device, con.A)
		
	return True


if __name__ == '__main__':
	main()
