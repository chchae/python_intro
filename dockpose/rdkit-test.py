import gzip
from rdkit import Chem


SDF_FILE = "/home/chchae/work/data/short.sdf"


def readfile( filename: str ) -> int :
    count : int = 0
    with  Chem.SDMolSupplier( filename ) as suppl:
        for mol in suppl:
            print( f"sending: {get_name(mol)} : {Chem.MolToSmiles(mol)}" )
            count += 1
            if 10 < count:
                break
        print( f"sender_func:end {count}-molecules" )
    return count



def get_name( mol ) -> str :
    if mol.HasProp( '_Name' ) and len( mol.GetProp( '_Name' ) ) > 0 :
        return mol.GetProp( '_Name' )
    elif mol.HasProp( 'chembl_id' ) :
        return mol.GetProp( 'chembl_id' )
    elif mol.HasProp( 'MolFileInfo' ) :
        return mol.GetProp( 'MolFileInfo' )
    return "_"


def main() :
    readfile( SDF_FILE )


if __name__ == "__main__" :
    main()

