from hdbcli import dbapi

from config.configuration import configs
from services.decorators import timing

SCHEMA = configs['hana.schema']


def get_hana_connection():
    return dbapi.connect(
        address=configs['hana.address'],
        port=configs['hana.port'],
        user=configs['hana.user'],
        password=configs['hana.password'],
        encrypt=True,
        sslValidateCertificate=True
    )


@timing(print_args=False)
def retrieve_relevant_chunks(query_embedding, top_k=3):
    connection = get_hana_connection()
    cursor = connection.cursor()
    allowed_sections = [contextSec['section'] for contextSec in configs['hana.embedding.contextSections']]
    sections_placeholder = ', '.join(['?'] * len(allowed_sections))
    combined_query = f"""
            WITH RankedDocuments AS (
                SELECT document_id,
                       ROW_NUMBER() OVER (ORDER BY COSINE_SIMILARITY(embedding, TO_REAL_VECTOR(?)) DESC) AS rank
                FROM {SCHEMA}.embeddings
            )
            SELECT e.document_id, k.link, e.section, e.text 
            FROM {SCHEMA}.embeddings e 
            JOIN {SCHEMA}.kbas k ON e.document_id = k.document_id
            WHERE e.document_id IN (
                SELECT document_id 
                FROM RankedDocuments 
                WHERE rank <= {top_k}
            )
            AND e.section IN ({sections_placeholder})
            ORDER BY e.chunk_id 
            """
    cursor.execute(combined_query, (str(query_embedding).replace(" ", ""), *allowed_sections))
    return cursor.fetchall()

# prompt = "de.hybris.platform.servicelayer.exceptions.UnknownIdentifierException: CatalogVersion with catalogId '_boconfig' and version 'hidden' not found!"