#!/usr/bin/env python3
"""Serve the pinned native UI while keeping runtime changes in managed profiles."""
import argparse
import importlib
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent.parent
# Chat, cancellation, token counts and shared sampling are native UI features.
# Loading, context edits and self-updates must go through validated launchers.
ALLOWED_POSTS={'/v1/chat/completions','/v1/messages','/v1/completions','/v1/responses',
               '/v1/messages/count_tokens','/v1/strata/cancel','/api/tokens','/settings','/mcp'}


def install_guard(server):
    original=server.make_handler
    def make_handler(service):
        native=original(service)
        class ManagedUI(native):
            def do_POST(self):
                path=urlsplit(self.path).path.rstrip('/')
                if path not in ALLOWED_POSTS:
                    self._json(409,{'error':{'message':'This backend uses a validated managed profile. Change its model, context or runtime through the managed launcher; Chat and Monitor remain available.','type':'managed_profile'}})
                    return
                return super().do_POST()
        return ManagedUI
    server.make_handler=make_handler
    if hasattr(server.Service,'context_limits'):
        limits=server.Service.context_limits
        def fixed_context(service):
            result=dict(limits(service))
            result.update(min=result['context'],max=result['context'])
            return result
        server.Service.context_limits=fixed_context


def main():
    parser=argparse.ArgumentParser(description=__doc__,add_help=False)
    parser.add_argument('--project',choices=['strata','maya','strata-dsv41'],required=True)
    args,remaining=parser.parse_known_args()
    project=ROOT/{'strata':'strata','maya':'maya/upstream','strata-dsv41':'strata-dsv41/upstream'}[args.project]
    sys.path.insert(0,str(project))
    sys.argv=[str(project/'serve/server.py'),*remaining]
    server=importlib.import_module('serve.server')
    install_guard(server)
    return server.main()


if __name__=='__main__':raise SystemExit(main())
