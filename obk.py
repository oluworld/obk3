#!/usr/bin/env python3
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
		properties = {'l': 'vfs:nlinks', 'u': 'vfs:uid', 'g': 'vfs:gid', 'z': 'vfs:filesize', 'i': 'vfs:inode'}
		x = properties[mode]
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
				x += ' /rdf1\n\tobk:error-during-readlink "%d"' % e.errno  # TODO test this
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
		properties = {'a': 'vfs:access-time', 'm': 'vfs:modify-time', 'c': 'vfs:create-time'}
		x = properties[mode]
		#
		buf = time.strftime("%Y_%m%b%d-%H:%M:%S", time.localtime(val))
		assert not not buf  # TODO: why do we need assert?
		# if not buf: DIE("strftime") # ??
		self.store.append(StringAttribute(x, buf))

	def add_checksum(self, a_sum):
		self.store.append(StringAttribute('obk:sha256', a_sum))
	
	def show_filename(self, out, name):
		pass
	
	def set_filename(self, name):
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


# class Output4(Output3):
# 	def _pd(self):
# 		pass


class Ror: pass


class Recurse(Ror):
	def __init__(self, path):
		self.path = path


class ResourceDef(Ror, object):
	def __init__(self, a_path):
		self.path = a_path
		self.sum = '<INVALID>'
		self.stat = ('<INVALID>',)
		
	def populate(self, a_controller):
		""" fill in self.stat and sum """
		filename = self.path
		
		if os.path.islink(filename):
			self.stat = os.lstat(filename)  # TODO:
		else:
			self.stat = os.stat(filename)
		if os.path.isdir(filename):  # stat.S_ISDIR(self.stat.st_mode):
			self.sum = '<DIR>'
		elif os.path.islink(filename):  # only for symlinks
			self.sum = '<isLINK>'
		else:
			# dont calculate checksums twice for hardlinks
			if self.stat.st_nlink > 1 and self.stat.st_ino in a_controller.nodes:
				self.sum = a_controller.nodes[self.stat.st_ino]
			else:
				try:
					xf = dfile(open(filename, 'rb'), None)  # TODO: None was self
					self.sum = _sha256(xf.read()).hexdigest()
				except Exception as e:
					print('-----------------------------')
					print('during sha256sum of %s' % filename)
					print('-----------------------------')
					print(e)
					print('-----------------------------')
				else:
					a_controller.nodes[self.stat.st_ino] = self.sum
					xf.close()
	
		# ~ R.name = a_filename
		# ~ print 167, R.path, R.sum
		
	__slots__ = ('path', 'stat', 'sum')


def newFile(a_con):
	return a_con.nextHNode()


def show_resource_def(a_resource_def, a_output, a_controller):
	"""@sig public static void show_resource_def(ResourceDef rdef, Output3 O, Controller c)"""
	s = a_resource_def.stat
	attr_store = AttributeStore()
	a_controller.A = attr_store    # must reset
	#
	attr_store.set_filename(a_resource_def.path)
	#
	attr_store.add_octal('p', s.st_mode & PERM_MASK, (s, a_resource_def.path))
	attr_store.add_long('i', s.st_ino)
	attr_store.add_long('l', s.st_nlink)
	attr_store.add_long('u', s.st_uid)
	attr_store.add_long('g', s.st_gid)
	if a_resource_def.sum[0] != '<':  # size of dirs and symlinks dont matter
		attr_store.add_long('z', s.st_size)
	attr_store.add_time('a', s.st_atime)
	attr_store.add_time('m', s.st_mtime)
	attr_store.add_time('c', s.st_ctime)
	if a_resource_def.sum[0] != '<':  # a_sum of dirs and symlinks dont exist
		attr_store.add_checksum(a_resource_def.sum)  # , 0)
	a_output.write('\n\n')


def postprocess_resource_def(a_resource_def, a_controller):
	"""@sig public static void postprocess_resource_def(ResourceDef a1, Controller a2)"""
	if a_resource_def.sum == '<DIR>':
		a_controller.put(Recurse(a_resource_def.path))
		a_controller.gg.Assert('fo', '1')
	else:
		a_controller.gg.Assert('fo', '0')


def main(args):
	output3 = Output3()
	output3.start()
	# G      = G0 # !!
	asserter = G('ii')
	# key  = [ os.path.join(sd, x ) for x in os.listdir(sd) for sd in xx ] # TODO: create filenamesource
	con = Controller(asserter, output3)
	rr = [go(sd, con) for sd in args]
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
		
	def nextHNode(self) -> str:
		""" allocate a node in the system and return an identifier for use with obk:storage """
		# TODO should be using a library for this and checking for duplicates anyway
		fn = name_of_inode(Fill(repr(self.last_inode)), self._root, cm_content)
		self.last_inode += 1
		self.gg.Assert('nf', fn)
		return fn

	__slots__ = ('resource_number', 'nodes', 'gg', 'O', 'A', 'last_inode', '_root', '__i')


class RecursionFlowControl(Exception):
	__slots__ = ('K', 'N')


def go(sd, con):
	try:
		i = 0
		t = True
		key = [os.path.join(sd, x) for x in os.listdir(sd)]  # TODO: create filenamesource
		con.putAll([ResourceDef(k) for k in key])
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
	elif isinstance(y, ResourceDef):
		output_device = sys.stdout
		
		resource_def = y
		resource_def.populate(con)
		
		show_resource_def(resource_def, output_device, con)
		postprocess_resource_def(resource_def, con)
		con.resource_number += 1
		con.O.show_attributes(con, output_device, con.A)
		
		return True


if __name__ == '__main__':
	# TODO argparse or getopt some options
	xx = sys.argv[1:] or ['.']
	main(xx)
