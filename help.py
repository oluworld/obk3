cm_content,cm_meta=0,1

def iswc(s,c='/',z=2):
	R=''  ## -typemark- string x len=len(s)+len(c)*len(s)/z
	x=0   ## -typemark- pos-int x
	for each in s:
		R=R+each
		if x == z-1:
			x=0
			R=R+c
		else:
			x=x+1
	assert len(R)==len(s)+len(c)*len(s)/z
	return R[:-1]
def name_of_inode(inode_str, X, cm=0):
	# returns a string
	# metadata is 1 (in cm)
	if cm == cm_content:
		CM = '-C'
	else:
		CM = '-M'
	R='%s/%s/%s%s'%(X._root,iswc(inode_str)[:-3],inode_str,CM)
	return R
def Fill(n,c='0',s=8):
	return '%s%s'%(c*(s-len(n)),n)

# ------------------------------------

class dfile:
	def __init__(self, aa, oo):
		self.x = aa
		self.xx = []
		self._oo=oo
	def write(self, a):
		self.x.write(a)
		self.xx += [a]
	#def __getattr__(self, x): return getattr(self.x,x)
	def read(self, x=None):
		if x==None:
			return self.x.read()
		return self.x.read(x)
	def close(self):
		self.x.close()
		if len(self.xx):
			f=open('XX','a+b')
			f.writelines(self.xx) #[ f.write(x) for x in self.xx ]
			f.close()
	def W(self):
		print 'aaaaaa'
