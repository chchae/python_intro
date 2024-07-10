import oracledb


def valid_sequence( code, seq ) -> bool :
    if 0 < len(code) and 0 < len(seq) :
        return True
    return False


def db_create_table( cursor ) :
    try :
        cursor.execute( "drop table VirusSequence" )
    except :
        pass

    sql = """
        create table VirusSequence (
        code varchar2(50) primary key,
        description varchar2(400),
        sequence CLOB,
        isworking number(1) default (0),
        pdbfilename varchar2(100) default ('')
        )
        """
    try :
        cursor.execute( sql )
    except Exception as e :
        print(e)


def db_insert( cursor, code, descr, seq ) :
    if valid_sequence( code, seq ) :
        sql = f"INSERT INTO VirusSequence ( code, description, sequence ) VALUES ( :1, :2, :3 )"
        try :
            cursor.execute( sql, (code, descr, seq) )
        except Exception as e :
            print(e)


def db_count( cursor ) -> int :
    sql = "select count(code) from VirusSequence"
    cursor.execute( sql )
    return int( cursor.fetchone()[0] )


def split_titleline( line ) :
    (code, descr) = ( line[1:] ).split( '|', 1 )
    code = code.strip()
    descr = descr.strip()
    return code, descr


def main() :
    user = 'virusdb'
    password='virus4db'
    dsn='virusdb.camd.krict.re.kr/orcl'
    with oracledb.connect( user=user, password=password, dsn=dsn ) as conn :
        with conn.cursor() as cursor :
            db_create_table( cursor )
            cnt = 0
            with open( '/share/databases/Virus_DDP/NCBI/Virus_Sequecne_Alltype/sequences.fasta' ) as ifp :
                code = ""
                descr = ""
                seq = ""
                for line in ifp.readlines() :
                    if line.startswith( '>' ) :
                        if valid_sequence( code, seq ) :
                            db_insert( cursor, code, descr, seq )
                            cnt = cnt + 1
                            if 0 == (cnt % 1000) :
                                break

                        (code, descr) = split_titleline( line )
                        seq = ""

                    else :
                        seq += line.strip()
            
            conn.commit()
            count = db_count( cursor )
            print( f"\n--->total {count}-iterms inserted..." )



if __name__ == "__main__" :
    main()


