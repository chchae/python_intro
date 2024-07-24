import sys
import time
import gzip
# import os.path
# import sqlite3
# from contextlib import closing
import multiprocessing
from multiprocessing import cpu_count, Manager, Process
from rdkit import Chem
from concurrent.futures import ProcessPoolExecutor
from queue import Queue


if sys.platform == "darwin":
    SDF_FILE = "/Users/chchae/work/data/ChEMBL_Bacteria.sdf.gz"
else:
    # SDF_FILE = "/share/databases/ChEMBL/ChEMBL_Bacteria.sdf.gz"
    # SDF_FILE = "/share/databases/ChEMBL/ChEMBL_32/chembl_32.sdf.gz"
    SDF_FILE = "/home/chchae/work/data/ChEMBL_Bacteria.sdf.gz"

QUERY_STRUCT = "N(C1=CC=CC=C1)C1=NC=NC2=CC=CC=C12"

# SdfMolecule = Chem.rdchem.Mol
SdfMolecule = str



def sender_func( tx: Queue[SdfMolecule], filename: str ) -> int :
    print( f"sender_func:start file=[{filename}]" )
    count : int = 0
    with  Chem.ForwardSDMolSupplier( gzip.open( filename ) ) as suppl:
        for mol in suppl:
            # tx.put( mol )
            tx.put( Chem.MolToSmiles(mol) )
            # print( f"sending: {Chem.MolToSmiles(mol)}" )
            count += 1
            # if 200 < count:
            #     break
        send_blank_mole( tx, 64 )       # send terminate signal to receivers
        print( f"sender_func:end {count}-molecules" )
    return count


def send_blank_mole( tx: Queue[SdfMolecule], count: int ) :
    for _ in range(count) :
        # mol = Chem.MolFromSmiles("")
        # tx.put( mol )
        tx.put( "" )
        # time.sleep( 1 )

def get_name( mol: SdfMolecule ) -> str :
    if mol.HasProp( '_Name' ) :
        return mol.GetProp( '_Name' )
    elif mol.HasProp( 'chembl_id' ) :
        return mol.GetProp( 'chembl_id' )
    elif mol.HasProp( 'MolFileInfo' ) :
        return mol.GetProp( 'MolFileInfo' )
    return "_"


def receiver_func( rx: Queue[SdfMolecule], query: SdfMolecule, jobid: int ) -> list[str] :
    # print( f"receiver_{jobid:02}:start" )
    results: list[str] = []
    while True :
        # mol: SdfMolecule = rx.get()
        mol: SdfMolecule = Chem.MolFromSmiles( rx.get() )
        if 0 == mol.GetNumAtoms() :     # if null molecule, terminate
            print( f"receiver_{jobid:02}: blank-molecules" )
            time.sleep( 1 )
            break

        # print( f"recv_{jobid:02}: {Chem.MolToSmiles(mol)}" )
        if mol.HasSubstructMatch( query ) :
            smi: str = Chem.MolToSmiles(mol)
            name: str = get_name( mol )
            print( f"{jobid:02} : {name} {smi}" )
            results.append( name )
    print( f"receiver_{jobid:02}:terminate with {len(results)}-results, {results}"  )
    return results


def save_to_db_closure( dbfilename: str ) :

    def save_func( mol: SdfMolecule ) :
        pass
    return save_func


# def create_database( dbfilename: str ) :
#     with closing( sqlite3.connect( dbfilename ) ) as conn :
#         with closing( conn.cursor() ) as cursor :
#             cursor.execute( "DROP   TABLE IF EXISTS fish" )
#             cursor.execute( "CREATE TABLE dockmols( name TEXT, smiles TEXT )" )
#         conn.commit()
#         print( f'ROWS affected : {conn.total_changes = }' )

# def make_database_file( dbfname: str ) :
#     if os.path.isfile( dbfname ) :
#         os.remove(dbfname)
#     create_database( dbfname )


def search_by_queue() -> list[ list[str] ]:
    num_cpus : int = cpu_count()
    print( f"max_workers ={num_cpus}" )
    
    que: multiprocessing.Queue[SdfMolecule] = multiprocessing.Queue()
    sender = Process( target=sender_func, args=(que, SDF_FILE,) )
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



def search_by_queue_pool() -> list[ list[str] ]:
    num_cpus : int = cpu_count()
    print( f"max_workers ={num_cpus}" )
    
    with Manager() as manager:
        queue: Queue[SdfMolecule] = manager.Queue()

        with ProcessPoolExecutor(max_workers=num_cpus) as executor:
            sender = executor.submit( sender_func, queue, SDF_FILE )
            _count_sent = sender.result()
            
            query = Chem.MolFromSmiles( QUERY_STRUCT )
            workers = [ executor.submit( receiver_func, queue, query, id ) for id in range(1, num_cpus) ]
            results: list[ list[str] ] = [ worker.result() for worker in workers ]

    return results


def main() -> None :
    start = time.time()
    # dbfname = "dock.sqlite3"
    # make_database_file(dbfname)

    results: list[ list[str] ] = search_by_queue_pool()
    print( f"Done. {time.time() - start}-secs, {len(list(results))}-molecules...")
    print( [ r for row in results for r in row ] )


if __name__ == "__main__" :
    main()


