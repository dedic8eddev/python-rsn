import concurrent.futures
import csv
import os

import pandas as pd
from tqdm import tqdm


def append_row_to_csv(data: dict, file_path: str):
    """
    Append data to existed .csv file in path or create if not exists
    """
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as f:
        field_names = list(data.keys())
        writer = csv.DictWriter(f,
                                delimiter=',',
                                lineterminator='\n',
                                fieldnames=field_names
                                )

        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def execute_task(task, iterator, concurrency=10, **kwargs):
    """
    The method executes the 'task' for each iterator element in multi-thread mode.

    Returns:
        pandas dataframe errors(arg, message) object with two columns:
            - arg: The argument passed to task
            - message: Error message

    Example:
        errors_df = execute_task(
                    task=self.process_image,
                    iterator=images,
                    crop_transparency=crop_transparency,
                    full_image=full_image,
                    thumb_image=thumb_image,
                    square_image=square_image
        )

        errors_df = execute_task(self.inspect_thumb, iterator=thumbs_urls)

    :param task: function to execute
    :param iterator: iterator to process row by row
    :param concurrency: max count of workers
    :param kwargs: passed to config progress bar
    """

    errors = []
    with tqdm(total=len(iterator)) as bar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(task, obj, **kwargs): obj
                for obj in iterator
            }
            results = {}
            for future in concurrent.futures.as_completed(futures):
                try:
                    arg = futures[future]
                    results[arg] = future.result()
                    bar.update(1)
                except Exception as exc:
                    fail_row = [
                        str(arg),
                        exc
                    ]
                    errors.append(fail_row)
                    bar.update(1)

    return pd.DataFrame(errors, columns=['arg', 'message'])
