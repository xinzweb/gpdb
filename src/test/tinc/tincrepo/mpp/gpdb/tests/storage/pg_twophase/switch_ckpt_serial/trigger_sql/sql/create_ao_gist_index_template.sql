-- start_ignore
SET gp_create_table_random_default_distribution=off;
-- end_ignore
CREATE INDEX pg2_ao_gist_idx1_template ON pg2_ao_table_gist_index_template USING GiST (property);
