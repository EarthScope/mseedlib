from .msrecord_buffer_reader import MS3RecordBufferReader
from .msrecord import binary_compare_records, logically_compare_records


def sort_mseed_content(content: bytes) -> bytes:
    """
    Sort miniSEED content bytes

    Args:
        content (bytes): The miniSEED content to sort.

    Returns:
        bytes: Sorted miniSEED content.
    """
    record_array = bytearray(content)
    source_id_starttime_record_triplet = []
    with MS3RecordBufferReader(record_array) as msreader:
        for msr in msreader:
            # Copy properties to avoid ctype issues
            source_id_starttime_record_triplet.append(
                (
                    msr.sourceid,
                    msr.starttime,
                    msr.record,
                )
            )

    # x[0]:source_id x[1]: starttime
    source_id_starttime_record_triplet.sort(key=lambda x: (x[0], x[1]))

    reordered_records = b"".join(r for _, _, r in source_id_starttime_record_triplet)

    return reordered_records


def compare_miniseed_content(
    content1: bytes, content2: bytes, ignore_order: bool = True
) -> [bool, dict]:
    """
    Compare two miniSEED content bytes for logical equality

    Note if doing exact binary comparison, use `content1 == content2`.

    Args:
        content1 (bytes): First miniSEED content.
        content2 (bytes): Second miniSEED content.

    Returns:
        bool: True if contents are equal, False otherwise.
    """

    if ignore_order:
        content1 = sort_mseed_content(content1)
        content2 = sort_mseed_content(content2)

    binary_compare_list = []
    logical_compare_list = []
    with (
        MS3RecordBufferReader(
            bytearray(content1), unpack_data=True
        ) as content1_msreader,
        MS3RecordBufferReader(
            bytearray(content2), unpack_data=True
        ) as content2_msreader,
    ):
        for msr1, msr2 in zip(content1_msreader, content2_msreader):
            binary_compare_list.append(binary_compare_records(msr1, msr2))
            logical_compare_list.append(logically_compare_records(msr1, msr2))
    return binary_compare_list, logical_compare_list
