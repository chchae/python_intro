import numpy as np
import pandas as pd



def get_dataset( size : int = 102_400 ) -> pd.DataFrame :
    df = pd.DataFrame()
    df['position'] = np.random.choice( ['left', 'middle', 'right' ], size )
    df['age'] = np.random.randint( 1, 50, size )
    df['team'] = np.random.choice( [ 'red', 'blue', 'yellow', 'green' ], size )
    df['win'] = np.random.choice( [ 'yes', 'no' ], size )
    df['prob'] = np.random.uniform( 0, 1, size )
    return df



def main() -> None :
    d1 = get_dataset( 1024 )
    #print( d1 )

    d2 = d1.groupby( [ 'team', 'position', 'win' ] )['age'].max()
    #print( d2 )

    d3 = d2.rank(method='max').sort_values()
    print( ", ".join( '%2d'%x for x in d3 ), "\n" )
    print( d3, "\n\n" )



if "__main__" == __name__ :
    main()

