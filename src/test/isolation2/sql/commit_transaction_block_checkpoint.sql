CREATE EXTENSION IF NOT EXISTS gp_inject_fault;

-- TEST 1: block checkpoint on segments

-- pause the 2PC after setting inCommit flag
select gp_inject_fault('twophase_transaction_commit_prepared', 'suspend', 3);

-- trigger a 2PC, and it will block at commit;
2: checkpoint;
2: begin;
2: create table t_commit_transaction_block_checkpoint (c int) distributed by (c);
2&: commit;

-- do checkpoint on segment content 1 in utility mode, and it should block
1U&: checkpoint;

-- resume the 2PC after setting inCommit flag
select gp_inject_fault('twophase_transaction_commit_prepared', 'reset', 3);
2<:
1U<:

-- TEST 2: block checkpoint on master

-- pause the CommitTransaction right before persistent table cleanup after
-- notifyCommittedDtxTransaction()
select gp_inject_fault('onephase_transaction_commit', 'suspend', 1);

-- trigger a 2PC, and it will block at commit;
2: checkpoint;
2: begin;
2: drop table t_commit_transaction_block_checkpoint;
2&: commit;

-- do checkpoint on master in utility mode, and it should block
-1U&: checkpoint;

-- resume the 2PC
select gp_inject_fault('onephase_transaction_commit', 'reset', 1);
2<:
-1U<:
