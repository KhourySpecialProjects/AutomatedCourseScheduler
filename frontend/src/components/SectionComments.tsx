import { useEffect, useMemo, useState } from 'react';
import { getAutomatedCourseSchedulerAPI, type CommentResponse, type UserResponse } from '../api/generated';

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function SectionComments({ sectionId }: { sectionId: number }) {
  const [me, setMe] = useState<UserResponse | null>(null);
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [replyPosting, setReplyPosting] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const byId = useMemo(() => new Map(comments.map((c) => [c.comment_id, c])), [comments]);
  const threads = useMemo(() => comments.filter((c) => c.parent_id === null), [comments]);

  const repliesFor = (parentId: number) => comments.filter((c) => c.parent_id === parentId);

  type CommentWithUser = CommentResponse & {
    user?: {
      user_id: number;
      first_name: string;
      last_name: string;
      email: string;
    };
  };

  function authorLabel(c0: CommentResponse): string {
    const c = c0 as CommentWithUser;
    const full = `${c.user?.first_name ?? ''} ${c.user?.last_name ?? ''}`.trim();
    const base = full || c.user?.email || `User ${c.user_id}`;
    if (me && c.user_id === me.user_id) return `${base} (you)`;
    return base;
  }

  async function refresh() {
    setError(null);
    setLoading(true);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      const [u, cs] = await Promise.all([api.getMeApiUsersMeGet(), api.getCommentsCommentsSectionIdGet(sectionId)]);
      setMe(u);
      setComments(cs);
    } catch {
      setError('Failed to load comments.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionId]);

  async function postComment() {
    if (!me) {
      setError('You must be signed in to comment.');
      return;
    }
    const text = content.trim();
    if (!text) return;
    setPosting(true);
    setError(null);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      await api.postCommentCommentsPost({
        section_id: sectionId,
        user_id: me.user_id,
        content: text,
      });
      setContent('');
      await refresh();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to post comment.');
    } finally {
      setPosting(false);
    }
  }

  async function deleteComment(commentId: number) {
    if (!me) return;
    setDeleting(commentId);
    setError(null);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      await api.deleteCommentCommentsCommentIdDelete(commentId);
      await refresh();
    } catch {
      setError('Failed to delete comment.');
    } finally {
      setDeleting(null);
    }
  }

  async function postReply(parentId: number) {
    if (!me) {
      setError('You must be signed in to reply.');
      return;
    }
    const text = replyContent.trim();
    if (!text) return;
    setReplyPosting(true);
    setError(null);
    try {
      const api = getAutomatedCourseSchedulerAPI();
      await api.postReplyCommentsParentIdPost(parentId, {
        section_id: sectionId,
        user_id: me.user_id,
        content: text,
      });
      setReplyContent('');
      setReplyingTo(null);
      await refresh();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to post reply.');
    } finally {
      setReplyPosting(false);
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Comments</h3>
        {loading ? <span className="text-xs text-gray-400">Loading…</span> : null}
      </div>

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {threads.length === 0 && !loading ? (
          <div className="text-sm text-gray-400 italic">No comments yet.</div>
        ) : (
          threads.map((c) => (
            <div key={c.comment_id} className="border border-gray-100 rounded-lg p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs text-gray-500">
                  <span className="font-medium text-gray-700">{authorLabel(c)}</span>
                  <span className="mx-2">·</span>
                  <span>{formatDate(c.created_at)}</span>
                </div>
                <div className="flex items-center gap-2">
                  {me && c.active && (
                    <button
                      type="button"
                      onClick={() => {
                        setError(null);
                        setReplyingTo((cur) => (cur === c.comment_id ? null : c.comment_id));
                        setReplyContent('');
                      }}
                      className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
                      title="Reply to this comment"
                    >
                      Reply
                    </button>
                  )}
                  {me && c.user_id === me.user_id && c.active && (
                    <button
                      type="button"
                      disabled={deleting === c.comment_id}
                      onClick={() => deleteComment(c.comment_id)}
                      className="text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-50"
                      title="Delete your comment"
                    >
                      {deleting === c.comment_id ? 'Deleting…' : 'Delete'}
                    </button>
                  )}
                  {c.resolved && (
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200">
                      Resolved
                    </span>
                  )}
                </div>
              </div>
              <div className={`mt-2 text-sm ${c.resolved ? 'text-gray-400' : 'text-gray-700'}`}>{c.content}</div>

              {replyingTo === c.comment_id && (
                <div className="mt-3 pl-3 border-l border-gray-100">
                  <textarea
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    rows={2}
                    placeholder="Write a reply…"
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <div className="mt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setReplyingTo(null);
                        setReplyContent('');
                      }}
                      className="px-3 py-2 text-xs font-medium bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => postReply(c.comment_id)}
                      disabled={replyPosting || replyContent.trim().length === 0}
                      className="px-3 py-2 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                    >
                      {replyPosting ? 'Replying…' : 'Post reply'}
                    </button>
                  </div>
                </div>
              )}

              {repliesFor(c.comment_id).length > 0 && (
                <div className="mt-3 space-y-2 pl-3 border-l border-gray-100">
                  {repliesFor(c.comment_id).map((r) => (
                    <div key={r.comment_id} className="text-sm text-gray-700">
                      <div className="flex items-center justify-between gap-2 mb-0.5">
                        <div className="text-xs text-gray-500">
                          <span className="font-medium text-gray-700">{authorLabel(r)}</span>
                          <span className="mx-2">·</span>
                          <span>{formatDate(r.created_at)}</span>
                        </div>
                        {me && r.user_id === me.user_id && r.active && (
                          <button
                            type="button"
                            disabled={deleting === r.comment_id}
                            onClick={() => deleteComment(r.comment_id)}
                            className="text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-50 shrink-0"
                            title="Delete your reply"
                          >
                            {deleting === r.comment_id ? 'Deleting…' : 'Delete'}
                          </button>
                        )}
                      </div>
                      {r.content}
                    </div>
                  ))}
                </div>
              )}

            </div>
          ))
        )}
      </div>

      <div className="mt-4">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          placeholder="Write a comment…"
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <div className="mt-2 flex justify-end">
          <button
            onClick={postComment}
            disabled={posting || content.trim().length === 0}
            className="px-3 py-2 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {posting ? 'Posting…' : 'Post comment'}
          </button>
        </div>
      </div>

      {/* Ensure TS uses byId in case we add reply UI soon */}
      <span className="hidden">{byId.size}</span>
    </section>
  );
}

