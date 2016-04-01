import topik

output_args = dict(source="http://localhost:9200", index="reddit_python_topik_smalls")
p = topik.TopikProject("reddit_python_smalls_test", output_type="ElasticSearchOutput",
                       output_args=output_args, content_field="text")
p.read_input(source="http://smalls:9200", index="reddit_python", content_field="text", doc_type="comment")
p.tokenize(min_length=3, stop_regex='html')
p.vectorize()
p.run_model(ntopics=10)
p.visualize()