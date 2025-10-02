"use client";
export default function GlobalError({error}:{error:Error}){
  return <div className='py-20 text-center'>Something went wrong: {error.message}</div>
}
