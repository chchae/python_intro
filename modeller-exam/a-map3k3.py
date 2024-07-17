from modeller import *
from modeller.automodel import *

log.verbose()
env = Environ()

env.io.atom_files_directory = ['.', '../atom_files']


env.libs.topology.read('${LIB}/top_heav.lib')
env.libs.parameters.read('${LIB}/par.lib')

aln = Alignment(env)
code='4bf2'
m = Model(env,file='4bf2')
# m.write( file='sequence.pdb' )
aln.append_model( m, align_codes=code )

target_sequence='WRRGKLLGQGAFGRVYLCYDVDTGRELASKQVQFDPDSPETSKEVSALECEIQLLKNLQHERIVQYYGCLRDRAEKTLTIFMEYMPGGSVKDQLKAYGALTESVTRKYTRQILEGMSYLHSNMIVHRDIKGANILRDSAGNVKLGDFGASKRLQTICMSGTGMRSVTGTPYWMSPEVISGEGYGRKADVWSLGCTVVEMLTEKPPWAEYEAMAAIFKIATQPTNPQLPSHISEHGRDFLRRIFVEARQRPSAEELLTHHFA'

aln.append_sequence( target_sequence )
# aln.write( file='alignment.seq' )

aln.align()
aln.write( file='alignment.ali' )


a = AutoModel(env,
              alnfile  = 'alignment.ali',
              knowns   = '4bf2',
              sequence = '')
a.make()

