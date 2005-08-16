# TODO:
# * vfs:parent
# * stop using res(%d)
# * move more logic into alvo
# * use alvo for postprocessing, (actual file operations)
#   * actually integrate HiStore
#   * move files into place (poss. across filesystems)

import os, time, stat, sha, sys
from help import *
#from alvo import *

try:
	from java.lang import Object as object
except:
	pass

PERM_MASK=00777

class G:
	def __init__(self, filename):
		if type(filename)==type(''):
			self.xx = open(filename,'w')
	def write(self,x):
		self.xx.write(x)
	def Assert(self, subj, pred):
		print >>self.xx, subj, pred

def xx(auid, agid):
	import pwd, grp
	uis=pwd.getpwuid(auid).pw_name
	gis=grp.getgrgid(agid).gr_name
	return uis, gis

class G0:
	def __init__(self, a=None): pass
	def write(self, x): pass
	def Assert(self, subj, pred): pass

# --------------------------------------------------------------
#                              .
# --------------------------------------------------------------

class Output3:
	def start(self):
		pass
	def show_long(self, out, T, val):
		""" based on show_diff_lines_long in eachfile.c """
		#
		if   T=='l': x=' vfs:nlinks'
		elif T=='u': x=' vfs:uid'
		elif T=='g': x=' vfs:gid'
		elif T=='z': x=' vfs:filesize'
		elif T=='i': x=' vfs:inode'
		#
		out.write('\t %s %ld /rdf1\n' % (x,val))

	def show_octal(self, out, _T, val, extra):
		x=''
		#
		s,p=extra
		#
		assert _T == 'p' # for mode
		#
		if stat.S_ISLNK(s.st_mode): # for a symlink ...
			x+=' vfs:symlink true /rdf1 '
			# TODO: catch errors here!!!
			try:
				read1=os.readlink(p)
				x+=' vfs:symtarget "%s"' % read1
			except OSError,e:
				x+=' /rdf1\n\tobk:error-during-readlink "%d"'%e.errno
			assert val==0777
		else:
			if stat.S_ISDIR(s.st_mode): # for a dir ...
				x+=' vfs:directory true /rdf1 '
			x+=' vfs:mode 8#%lo'%val
		#
		out.write(' %s /rdf1\n'%x)

	def show_time(self, out, T, val):
		""" based on show_diff_time from eachfile.c """
		#
		if   T=='a': x=' vfs:access-time'
		elif T=='m': x=' vfs:modify-time'
		elif T=='c': x=' vfs:create-time'
		#
		buf=time.strftime("%Y%m%d-%H%M%S", time.localtime(val))
		assert not not buf #TODO:
		#if not buf: DIE("strftime") # ??
		out.write('\t %s "%s" /rdf1\n' % (x,buf))

	def show_checksum(self, out, sum):
		out.write("\tobk:sha1 '%s' /rdf1\n" %(sum))

	def show_filename(self, out, name):
		pass

	def set_filename(self, out, name, a_con):
		_res='res%d' % a_con.resource_number
		a_con.gg.Assert('fn',name)
		xx = newFile(a_con)
		out.write('%s obk:res "%s" /rdf1\n  obk:storage "%s" /rdf1\n\t'% (_res, name, xx))

class Output4(Output3):
	def _pd(self):
		pass


class ResourceDef(object):
	__slots__=['path','stat','sum']
	#
	def __init__(self, a_path):
		self.path = a_path
		self.sum  = '<INVALID>'
		self.stat = ('<INVALID>',)

def mk_resource_def(a_filename, a_controller):
	"@sig public ResourceDef mk_resource_def(String s, Controller c)"
	R = ResourceDef(a_filename)
	#
	if os.path.islink(a_filename): R.stat = os.lstat(a_filename) # TODO:
	else: R.stat = os.stat(a_filename)
	if os.path.isdir(a_filename):#stat.S_ISDIR(self.stat.st_mode):
		R.sum = '<DIR>'
	elif os.path.islink(a_filename): # only for symlinks
		R.sum = '<isLINK>'
	else:
		# dont calculate checksums twice for hardlinks
		if R.stat.st_nlink > 1 and R.stat.st_ino in a_controller.nodes:
				R.sum = a_controller.nodes[R.stat.st_ino]
		else:
				try:
					xf=dfile(open(a_filename),None) # TODO: None was self
					R.sum = sha.new(xf.read()).hexdigest()
				except Exception, e:
					print '-----------------------------'
					print 'during %s'%a_filename
					print '-----------------------------'
					print e
					print '-----------------------------'
				else:
					a_controller.nodes[R.stat.st_ino] = R.sum
					xf.close()
	#~ R.name = a_filename
	#~ print 167, R.path, R.sum
	return R

def newFile(a_con):
	""" allocate a node in the system and return an identifier for use with obk:storage """
	fn=name_of_inode(Fill(`a_con.last_inode`),a_con,cm_content)
	a_con.last_inode += 1
	a_con.gg.Assert('nf',fn)
	return fn

def show_resource_def(a_resource_def, a_output, a_controller):
	"@sig public static void show_resource_def(ResourceDef rdef, Output3 O, Controller c)"
	s      = a_resource_def.stat
	O      = a_controller.O # !!
	#
	O.set_filename(a_output, a_resource_def.path, a_controller)
	#
	O.show_octal(a_output, 'p', s.st_mode & PERM_MASK, (s,a_resource_def.path))
	O.show_long(a_output, 'i', s.st_ino)
	O.show_long(a_output, 'l', s.st_nlink)
	O.show_long(a_output, 'u', s.st_uid)
	O.show_long(a_output, 'g', s.st_gid)
	if a_resource_def.sum[0] != '<': # size of dirs and symlinks dont matter
		O.show_long(a_output, 'z', s.st_size)
	O.show_time(a_output, 'a', s.st_atime)
	O.show_time(a_output, 'm', s.st_mtime)
	O.show_time(a_output, 'c', s.st_ctime)
	if a_resource_def.sum[0] != '<': # sum of dirs and symlinks dont exist
		O.show_checksum(a_output, a_resource_def.sum)#, 0)
	a_output.write("\tobk:dummy 'dummy' /rdf0\n")

def postprocess_resource_def(a_resource_def, a_controller):
	"@sig public static void postprocess_resource_def(ResourceDef a1, Controller a2)"
	if a_resource_def.sum == '<DIR>': # and recursive and(or??) name in vals
		#go(os.path.join(a_resource_def.path), a_controller.O, a_controller.gg)
		a_controller.put(['recursion',a_resource_def.path])
		a_controller.gg.Assert('fo','1')
	else:
		a_controller.gg.Assert('fo','0')

def main():
	O       = Output3()
	O.start()
	xx      = sys.argv[1:] or ['.']
	#G      = G0 # !!
	gg      = G('ii')
	#key  = [ os.path.join(sd, x ) for x in os.listdir(sd) for sd in xx ] # TODO: create filenamesource
	con     = Controller(gg, O)
	#con._i=key
	#go(con)
	rr      = [ go(sd,con) for sd in xx ]
	rr=rr

class Controller(object):
	def __init__(self, gg, O):
		self.resource_number = 1
		self.nodes      = {}
		self.gg         = gg
		self.O          = O
		self.last_inode = 0
		self._root      = time.strftime('%d%H%M%S', time.localtime(time.time()))
		self._i         = []
	def get(self, i):
		"@sig public String get(int i)" # throws...
		return self._i[i]
	def put(self, v):
		"@sig public void put(String v)"
		self._i.append(v)

class RecursionFlowControl: pass

def go(sd,con):
	try:
		key  = [ os.path.join(sd, x ) for x in os.listdir(sd)] # TODO: create filenamesource
		con._i+=key
		go1(None,con,0)
	except RecursionFlowControl, rfc:
		#key  = [ os.path.join(sd, x ) for x in os.listdir(sd)] # TODO: create filenamesource
		#con._i=con._i[rfc.N+1:]+key
		#go1(
		con._i=con._i[rfc.N+1:] # save memory
		go(rfc.K, con)
	except IndexError:
		pass # presumably from con.get(xx)

def go1(sd,con,n):
	y=con.get(n)
	if y[0]=='recursion': # TODO: use currying and a behavior. hint: lambda
		rfc=RecursionFlowControl()
		rfc.K=y[1]
		rfc.N=n
		raise rfc
	#
	val = mk_resource_def(y,con)
	if 1:
	#for val in vals:
		show_resource_def(val, sys.stdout, con)
		postprocess_resource_def(val, con)
		con.resource_number += 1
	try:
		go1(sd,con,n+1)
	except Exception, e:
		print 100, 'error during operation >>', (sd,con,n), '<<', e 

if __name__ == '__main__':
	main()
