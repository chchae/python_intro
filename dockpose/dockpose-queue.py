import sys
import time
import gzip
# import os.path
# import sqlite3
# from contextlib import closing
import multiprocessing
import rdkit
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

SdfMolecule = Chem.rdchem.Mol



def sender_func( tx: Queue[SdfMolecule], filename: str ) -> int :
    print( f"sender_func:start file=[{filename}]" )
    count : int = 0
    with  Chem.ForwardSDMolSupplier( gzip.open( filename ) ) as suppl:
        # suppl.SetProcessPropertyLists(True)
        for mol in suppl:
            tx.put( mol )
            # print( f"sending: {Chem.MolToSmiles(mol)}" )
            count += 1
            # if 200 < count:
            #     break
        send_blank_mole( tx, 64 )       # send terminate signal to receivers
        print( f"sender_func:end {count}-molecules" )
    return count


def send_blank_mole( tx: Queue[SdfMolecule], count: int ) :
    for _ in range(count) :
        mol = Chem.MolFromSmiles("")
        tx.put( mol )
        # time.sleep( 1 )

def get_name( mol: SdfMolecule ) -> str :
    if mol.HasProp( '_Name' ) and len( mol.GetProp( '_Name' ) ) > 0 :
        return mol.GetProp( '_Name' )
    elif mol.HasProp( 'chembl_id' ) :
        return mol.GetProp( 'chembl_id' )
    elif mol.HasProp( 'MolFileInfo' ) :
        return mol.GetProp( 'MolFileInfo' )
    return "_"


def receiver_func( rx: Queue[SdfMolecule], query: SdfMolecule, jobid: int ) -> list[str] :
    def fibo(n : int) -> int :
        if n < 2 :
            return 1
        return fibo(n - 2) + fibo(n - 1)

    def find_mcs() :
        mol1 = Chem.MolFromSmiles("O=C(NCc1cc(OC)c(O)cc1)CCCC/C=C/C(C)C")
        mol2 = Chem.MolFromSmiles("CC(C)CCCCCC(=O)NCC1=CC(=C(C=C1)O)OC")
        mol3 = Chem.MolFromSmiles("c1(C=O)cc(OC)c(O)cc1")
        mol4 = Chem.MolFromSmiles("CC(C)CCCCCC(=O)NCC1=CC(=C(C=C1)O)OCCC")
        mol5 = Chem.MolFromSmiles("CC(C)(O1)C[C@@H](O)[C@@]1(O2)[C@@H](C)[C@@H]3CC=C4[C@]3(C2)C(=O)C[C@H]5[C@H]4CC[C@@H](C6)[C@]5(C)Cc(n7)c6nc(C[C@@]89(C))c7C[C@@H]8CC[C@@H]%10[C@@H]9C[C@@H](O)[C@@]%11(C)C%10=C[C@H](O%12)[C@]%11(O)[C@H](C)[C@]%12(O%13)[C@H](O)C[C@@]%13(C)CO")
        mol6 = Chem.MolFromSmiles("C[C@H]1[C@H]2CC=C3C2(COC14[C@@H](CC(O4)(C)C)O)C(=O)C[C@H]5[C@H]3CC[C@@H]6[C@@]5([C@H](C7=NC8=C(C[C@]9([C@H](C8)CC[C@@H]1[C@@H]9C[C@H]([C@]2(C1=C[C@H]1[C@@]2([C@@H](C2(O1)[C@@H](C[C@@](O2)(C)CO)O)C)O)C)O)C)N=C7C6)OC)C")
        mols = [mol1,mol2,mol3,mol4]
        mols = [mol5,mol6]
        from rdkit.Chem.rdFMCS import FindMCS
        FindMCS(mols)

    # print( f"receiver_{jobid:02}:start" )
    results: list[str] = []
    while True :
        mol: SdfMolecule = rx.get()
        if 0 == mol.GetNumAtoms() :     # if null molecule, terminate
            # print( f"receiver_{jobid:02}: blank-molecules" )
            time.sleep( 1 )
            break

        # find_mcs()
        # fibo(40)

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
    num_cpus : int = multiprocessing.cpu_count()
    print( f"max_workers ={num_cpus}" )
    
    que: multiprocessing.Queue[SdfMolecule] = multiprocessing.Queue()
    sender = multiprocessing.Process( target=sender_func, args=(que, SDF_FILE,) )
    sender.start()

    query = Chem.MolFromSmiles( QUERY_STRUCT )
    receivers: list[multiprocessing.Process] = [ multiprocessing.Process( target=receiver_func, args=(que, query, id) ) for id in range(1, num_cpus) ]
    for recv in receivers:
        recv.start()

    sender.join()
    print( "\nsender terminated" )
    for recv in receivers:
        recv.join()
    print( "\nall receivers terminated" )
    
    return []



def search_by_queue_pool() -> list[ list[str] ]:
    num_cpus : int = multiprocessing.cpu_count()
    print( f"max_workers ={num_cpus}" )
    
    with multiprocessing.Manager() as manager:
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


