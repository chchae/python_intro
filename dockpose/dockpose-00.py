import sys
import time
from typing import Generator, Callable
from multiprocessing import cpu_count, Process, Pipe, connection, Queue
from concurrent.futures import ThreadPoolExecutor
from rdkit import Chem
import gzip

if sys.platform == "darwin":
    SDF_FILE = "/Users/chchae/work/data/ChEMBL_Bacteria.sdf.gz"
else:
    SDF_FILE = "/share/databases/ChEMBL/ChEMBL_Bacteria.sdf.gz"
    SDF_FILE = "/home/chchae/work/data/ChEMBL_Bacteria.sdf.gz"

QUERY_STRUCT = "N(C1=CC=CC=C1)C1=NC=NC2=CC=CC=C12"


SdfMolecule = Chem.rdchem.Mol
SdfMoleculeGenerator = Generator[SdfMolecule, None, None]
SdfMoleculeFetcherFuncType = Callable[ [], SdfMoleculeGenerator ]
BuilderFuncType = Callable[ [SdfMolecule], int ]



def sender_func( tx: Queue, filename: str ) :
    with  Chem.ForwardSDMolSupplier( gzip.open( filename ) ) as suppl:
        count : int = 0
        for mol in suppl:
            tx.put( mol )
            # print( f"sending: {Chem.MolToSmiles(mol)}" )
            count += 1
            # if 200 < count:
            #     break
    send_blank_mole( tx, 64 )       # send terminate signal to receivers
    print( f"sender_func:end {count}-molecules" )


def send_blank_mole( tx: Queue, count: int ) :
    for _ in range(count) :
        mol = Chem.MolFromSmiles("")
        tx.put( mol )
        # time.sleep( 1 )


def receiver_func( rx: Queue, query: SdfMolecule, jobid: int ) :
    while True :
        mol: SdfMolecule = rx.get()
        if 0 == mol.GetNumAtoms() :     # if null molecule, terminate
            # print( f"receiver_{jobid:02}: blank-molecules" )
            time.sleep( 1 )
            break

        # print( f"recv_{jobid:02}: {Chem.MolToSmiles(mol)}" )
        if mol.HasSubstructMatch( query ) :
            smi: str = Chem.MolToSmiles(mol)
            # name: str = mol.GetProp("_Name")
            name = ""
            print( f"{jobid:02} : {name} {smi}" )
    # print( f"receiver_{jobid:02}:terminate" )



def search_by_queue() :
    num_cpus : int = cpu_count()
    print( f"max_workers ={num_cpus}" )

    que = Queue()
    sender = Process( target=sender_func, args=(que,SDF_FILE,) )
    sender.start()

    query = Chem.MolFromSmiles( QUERY_STRUCT )
    receivers: list[Process] = [ Process( target=receiver_func, args=(que, query, id) ) for id in range(1, num_cpus) ]
    for recv in receivers:
        recv.start()

    sender.join()
    print( "\nsender terminated" )
    for recv in receivers:
        recv.join()
    print( "\nall receivers terminated" )

    return []


def main() -> None :
    start = time.time()
    results = search_by_queue()
    print( f"Done.  {len(list(results))}-molecules, {time.time() - start}-secs...")


if __name__ == "__main__" :
    main()

